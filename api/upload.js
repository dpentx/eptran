import crypto from "node:crypto";

export const config = { maxDuration: 30 };

// Aynı anda sırada bekleyebilecek en fazla kitap sayısı (çevrilmekte olan hariç).
const MAX_QUEUE = 10;

// Paylaşılan bir yükleme şifresiyle basit ama etkili bir erişim kontrolü.
// Bu olmadan /api/upload'ı bilen HERKES (tarayıcı bile açmadan) bir
// queue/<slug> dalı açtırıp repo-geneli contents+actions yazma izinli
// gerçek bir GitHub token'ı alabiliyordu — bkz. güvenlik incelemesi
// notları. timingSafeEqual, şifre karşılaştırmasının süresinden şifrenin
// doğru kısmının tahmin edilebilmesini (timing attack) önlüyor.
function checkSecret(provided) {
  const expected = process.env.UPLOAD_SECRET;
  if (!expected) return false; // secret tanımlı değilse KİMSEYİ içeri alma
  const a = Buffer.from(String(provided || ""));
  const b = Buffer.from(expected);
  if (a.length !== b.length) return false;
  return crypto.timingSafeEqual(a, b);
}

// Kitap slug'ı — translate.py'deki book_slug hesabıyla BİREBİR aynı mantık.
function slugify(filename) {
  const noExt = filename.replace(/\.(epub|pdf)$/i, "");
  return noExt.replace(/[^\w-]/g, "_");
}

function base64url(buf) {
  return Buffer.from(buf)
    .toString("base64")
    .replace(/\+/g, "-")
    .replace(/\//g, "_")
    .replace(/=+$/, "");
}

// GitHub App için kısa ömürlü bir JWT imzalar (RS256). Ek npm paketi
// gerektirmesin diye Node'un yerleşik crypto modülüyle elle yapılıyor.
function buildAppJwt(appId, privateKey) {
  const now = Math.floor(Date.now() / 1000);
  const header = { alg: "RS256", typ: "JWT" };
  // iat'ı 30sn geriden başlatmak saat senkron sapmalarına karşı GitHub'ın
  // önerdiği bir pratik; exp en fazla 10dk olabiliyor, 9dk kullanıyoruz.
  const payload = { iat: now - 30, exp: now + 540, iss: appId };
  const unsigned = `${base64url(JSON.stringify(header))}.${base64url(JSON.stringify(payload))}`;
  const signature = crypto.createSign("RSA-SHA256").update(unsigned).sign(privateKey);
  return `${unsigned}.${base64url(signature)}`;
}

// Sadece BU repo'ya, sadece Contents+Actions yazma iznine sahip, ~1 saat
// sonra kendiliğinden ölen bir kurulum token'ı üretir. APP_ID/
// APP_PRIVATE_KEY tanımlı değilse null döner (çağıran taraf ele alır).
async function getScopedUploadToken(repo) {
  const appId = process.env.APP_ID;
  const privateKey = (process.env.APP_PRIVATE_KEY || "").replace(/\\n/g, "\n");
  if (!appId || !privateKey) return null;

  const jwt = buildAppJwt(appId, privateKey);
  const ghApp = (path, opts = {}) =>
    fetch(`https://api.github.com${path}`, {
      ...opts,
      headers: {
        Authorization: `Bearer ${jwt}`,
        Accept: "application/vnd.github+json",
        ...(opts.headers || {}),
      },
    });

  const instRes = await ghApp("/app/installations");
  if (!instRes.ok) throw new Error("App installations alınamadı");
  const installations = await instRes.json();
  if (!installations.length) throw new Error("App hiçbir hesaba kurulu değil");
  const installationId = installations[0].id;

  const tokenRes = await ghApp(`/app/installations/${installationId}/access_tokens`, {
    method: "POST",
    body: JSON.stringify({
      repositories: [repo.split("/")[1]],
      permissions: { contents: "write", actions: "write" },
    }),
  });
  if (!tokenRes.ok) throw new Error("Kurulum token'ı alınamadı");
  const tokenData = await tokenRes.json();
  return tokenData.token;
}

async function listBranchNames(gh) {
  const res = await gh("/branches?per_page=100");
  if (!res.ok) throw new Error("Dal listesi alınamadı");
  return (await res.json()).map((b) => b.name);
}

// Bir queue/<slug> dalında dosya GERÇEKTEN yüklenmiş mi? (main'e göre en az
// 1 commit ilerde mi). Yükleme yarıda kalmış yetim dallar "hazır" sayılmaz.
// Hazırsa yüklemenin tarihi de döner (sıralama için).
async function uploadInfo(gh, mainBranch, name) {
  const res = await gh(`/compare/${mainBranch}...${name}`);
  if (!res.ok) return { name, ready: false, date: "" };
  const data = await res.json();
  const ready = (data.ahead_by || 0) > 0;
  const date = ready ? data.commits?.[0]?.commit?.committer?.date || "" : "";
  return { name, ready, date };
}

export default async function handler(req, res) {
  if (req.method !== "POST")
    return res.status(405).json({ error: "Method not allowed" });

  const REPO = process.env.GH_REPO;
  const TOKEN = process.env.GH_PAT;
  const MAIN_BRANCH = process.env.GH_BRANCH || "main";

  if (!REPO || !TOKEN)
    return res.status(500).json({ error: "Sunucu yapılandırması eksik" });

  const gh = (path, opts = {}) =>
    fetch(`https://api.github.com/repos/${REPO}${path}`, {
      ...opts,
      headers: {
        Authorization: `token ${TOKEN}`,
        "Content-Type": "application/json",
        ...(opts.headers || {}),
      },
    });

  const body = req.body || {};

  // Her iki aşama için de (start ve finalize) şifre zorunlu — yalnızca
  // start'ı korumak yetmez, çünkü finalize tek başına bilinen bir dalda
  // workflow tetiklemeye izin veriyor.
  if (!checkSecret(body.secret)) {
    return res.status(401).json({ error: "Yetkisiz" });
  }

  try {
    // İKİNCİ AŞAMA: dosya GitHub'a doğrudan (tarayıcıdan) yüklendikten
    // SONRA çağrılır — bu istek küçük (sadece dal adı), Vercel'in
    // boyut sınırına takılmaz.
    //
    // Sıraya ekleme: çevrilmekte olan bir kitap (book/*) ya da aynı anda
    // daha önce yüklenmiş başka bir bekleyen kitap varsa workflow BURADA
    // tetiklenmez; kitap queue/<slug> dalında bekler ve öndeki kitabın PR'ı
    // merge olup dalı silinince kendiliğinden başlatılır (bkz.
    // scripts/start_next_queue.py, delete-merged-book-branch.yml). Sadece
    // sistem boşsa workflow'u burada, uzun ömürlü sunucu token'ıyla
    // (GH_PAT) tetikliyoruz.
    if (body.action === "finalize") {
      const { branch } = body;
      if (!branch || !branch.startsWith("queue/"))
        return res.status(400).json({ error: "Geçerli bir queue dalı gerekli" });

      await new Promise((r) => setTimeout(r, 1500));

      const names = await listBranchNames(gh);
      if (!names.includes(branch))
        return res.status(404).json({ error: "Kuyruk dalı bulunamadı" });

      const mine = await uploadInfo(gh, MAIN_BRANCH, branch);
      if (!mine.ready)
        return res.status(409).json({ error: "Dosya dalda bulunamadı — yükleme tamamlanmamış" });

      // Önde kimler var: çevrilmekte olan kitap + benden ÖNCE yüklenmiş
      // bekleyenler (eşit tarihte ad sırası belirler — iki yükleme aynı
      // anda biterse ikisi de beklemeye düşmesin).
      const hasActiveBook = names.some((n) => n.startsWith("book/"));
      const others = names.filter((n) => n.startsWith("queue/") && n !== branch);
      const infos = await Promise.all(others.map((n) => uploadInfo(gh, MAIN_BRANCH, n)));
      const olderWaiting = infos.filter(
        (i) =>
          i.ready &&
          (i.date < mine.date || (i.date === mine.date && i.name < branch))
      ).length;
      const ahead = (hasActiveBook ? 1 : 0) + olderWaiting;

      if (ahead > 0) {
        return res.json({ success: true, queued: true, ahead });
      }

      const dispatchRes = await gh("/actions/workflows/translate.yml/dispatches", {
        method: "POST",
        body: JSON.stringify({ ref: branch }),
      });
      if (!dispatchRes.ok) {
        return res.status(500).json({ error: "Workflow tetiklenemedi" });
      }
      return res.json({ success: true, queued: false });
    }

    // BİRİNCİ AŞAMA (varsayılan): sadece dosya adı gönderilir, dosya
    // İÇERİĞİ YOK — Vercel'in 4.5MB istek sınırına buradan takılma
    // ihtimali yok. Burada:
    //  1) aynı kitap zaten çevriliyor/sırada mı bakılır; kuyruk doluysa reddedilir
    //  2) main'in ucundan queue/<slug> dalı açılır (main'e HİÇ yazılmaz)
    //  3) SADECE bu repoya, SADECE Contents+Actions iznine sahip, ~1 saat
    //     sonra kendiliğinden ölen bir token üretilip tarayıcıya verilir
    //
    // Tarayıcı bu token'la dosyayı GitHub'a DOĞRUDAN yükler (GitHub'ın
    // Contents API sınırı ~50-100MB — Vercel'in 4.5MB'lık sınırına
    // buradan takılmadan). Kalıcı GH_PAT hiçbir zaman tarayıcıya çıkmıyor;
    // çıkan token otomatik kendi kendine geçersizleşiyor ve tek bir
    // repo'yla sınırlı.
    const { filename } = body;
    if (!filename)
      return res.status(400).json({ error: "filename gerekli" });

    const isEpub = filename.endsWith(".epub");
    const isPdf = filename.endsWith(".pdf");
    if (!isEpub && !isPdf)
      return res.status(400).json({ error: "Sadece .epub ve .pdf dosyaları kabul edilir" });

    const slug = slugify(filename);
    const queueBranch = `queue/${slug}`;

    const names = await listBranchNames(gh);

    if (names.includes(`book/${slug}`))
      return res.status(409).json({ error: "Bu kitap zaten çevriliyor" });

    const hasActiveBook = names.some((n) => n.startsWith("book/"));
    const otherQueue = names.filter((n) => n.startsWith("queue/") && n !== queueBranch);
    const otherInfos = await Promise.all(otherQueue.map((n) => uploadInfo(gh, MAIN_BRANCH, n)));
    const waitingCount = otherInfos.filter((i) => i.ready).length;

    if (waitingCount >= MAX_QUEUE)
      return res.status(409).json({
        error: `Sıra dolu (en fazla ${MAX_QUEUE} kitap bekleyebilir)`,
      });

    const branchExists = names.includes(queueBranch);
    if (branchExists) {
      const mine = await uploadInfo(gh, MAIN_BRANCH, queueBranch);
      if (mine.ready)
        return res.status(409).json({ error: "Bu kitap zaten sırada" });
      // Dosya yok: daha önceki yarım kalmış bir yüklemenin yetim dalı —
      // yeniden kullanıyoruz, böylece aynı dosyayı tekrar denemek mümkün.
    } else {
      const refRes = await gh(`/git/ref/heads/${MAIN_BRANCH}`);
      if (!refRes.ok) {
        return res.status(500).json({ error: "main dalının referansı alınamadı" });
      }
      const refData = await refRes.json();
      const mainSha = refData.object.sha;

      const createRefRes = await gh("/git/refs", {
        method: "POST",
        body: JSON.stringify({ ref: `refs/heads/${queueBranch}`, sha: mainSha }),
      });
      if (!createRefRes.ok) {
        const err = await createRefRes.json();
        return res.status(500).json({ error: "Kuyruk dalı oluşturulamadı", detail: err.message });
      }
    }

    // Dalı biz açtıysak token üretilemezse geri sileriz; yeniden kullandığımız
    // yetim dala dokunmayız.
    const cleanupBranch = async () => {
      if (!branchExists) {
        await gh(`/git/refs/heads/${queueBranch}`, { method: "DELETE" }).catch(() => {});
      }
    };

    let uploadToken;
    try {
      uploadToken = await getScopedUploadToken(REPO);
    } catch (e) {
      await cleanupBranch();
      return res.status(500).json({ error: "Geçici yükleme token'ı üretilemedi", detail: e.message });
    }
    if (!uploadToken) {
      await cleanupBranch();
      return res.status(500).json({
        error: "APP_ID / APP_PRIVATE_KEY Vercel'de tanımlı değil (bkz. .github/workflows/translate.yml'deki aynı secret'lar — aynı değerleri Vercel proje ayarlarına da eklemen gerekiyor)",
      });
    }

    return res.json({
      repo: REPO,
      branch: queueBranch,
      token: uploadToken,
      queued: hasActiveBook || waitingCount > 0,
      position: waitingCount + 1,
    });
  } catch (err) {
    console.error(err);
    return res.status(500).json({ error: "Sunucu hatası" });
  }
}
