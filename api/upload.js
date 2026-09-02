import crypto from "node:crypto";

export const config = { maxDuration: 30 };

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

  try {
    // İKİNCİ AŞAMA: dosya GitHub'a doğrudan (tarayıcıdan) yüklendikten
    // SONRA çağrılır — bu istek küçük (sadece dal adı), Vercel'in
    // boyut sınırına takılmaz. Workflow'u burada, uzun ömürlü sunucu
    // token'ıyla (GH_PAT) tetikliyoruz.
    if (body.action === "finalize") {
      const { branch } = body;
      if (!branch) return res.status(400).json({ error: "branch gerekli" });

      await new Promise((r) => setTimeout(r, 1500));
      const dispatchRes = await gh("/actions/workflows/translate.yml/dispatches", {
        method: "POST",
        body: JSON.stringify({ ref: branch }),
      });
      if (!dispatchRes.ok) {
        return res.status(500).json({ error: "Workflow tetiklenemedi" });
      }
      return res.json({ success: true });
    }

    // BİRİNCİ AŞAMA (varsayılan): sadece dosya adı gönderilir, dosya
    // İÇERİĞİ YOK — Vercel'in 4.5MB istek sınırına buradan takılma
    // ihtimali yok. Burada:
    //  1) zaten devam eden bir çeviri var mı bakılır
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

    const branchesRes = await gh("/branches?per_page=100");
    if (branchesRes.ok) {
      const branches = await branchesRes.json();
      const active = branches.filter(
        (b) => b.name.startsWith("book/") || b.name.startsWith("queue/")
      );
      if (active.length > 0) {
        return res.status(409).json({ error: "Zaten devam eden bir çeviri var" });
      }
    }

    const slug = slugify(filename);
    const queueBranch = `queue/${slug}`;

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

    let uploadToken;
    try {
      uploadToken = await getScopedUploadToken(REPO);
    } catch (e) {
      await gh(`/git/refs/heads/${queueBranch}`, { method: "DELETE" }).catch(() => {});
      return res.status(500).json({ error: "Geçici yükleme token'ı üretilemedi", detail: e.message });
    }
    if (!uploadToken) {
      await gh(`/git/refs/heads/${queueBranch}`, { method: "DELETE" }).catch(() => {});
      return res.status(500).json({
        error: "APP_ID / APP_PRIVATE_KEY Vercel'de tanımlı değil (bkz. .github/workflows/translate.yml'deki aynı secret'lar — aynı değerleri Vercel proje ayarlarına da eklemen gerekiyor)",
      });
    }

    return res.json({ repo: REPO, branch: queueBranch, token: uploadToken });
  } catch (err) {
    console.error(err);
    return res.status(500).json({ error: "Sunucu hatası" });
  }
}
