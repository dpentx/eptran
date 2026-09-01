export const config = { maxDuration: 30 };

// Kitap slug'ı — translate.py'deki book_slug hesabıyla BİREBİR aynı
// mantık (aynı dosya adından her zaman aynı slug çıkmalı, yoksa
// translate.py başka bir isimle book/<slug> dalı açar ve bu dalın
// queue/<slug> ismiyle eşleşmesi bozulur).
function slugify(filename) {
  const noExt = filename.replace(/\.(epub|pdf)$/i, "");
  return noExt.replace(/[^\w-]/g, "_");
}

export default async function handler(req, res) {
  if (req.method !== "POST")
    return res.status(405).json({ error: "Method not allowed" });

  const { filename, content } = req.body;

  if (!filename || !content)
    return res.status(400).json({ error: "filename ve content gerekli" });

  const isEpub = filename.endsWith(".epub");
  const isPdf = filename.endsWith(".pdf");

  if (!isEpub && !isPdf)
    return res.status(400).json({ error: "Sadece .epub ve .pdf dosyaları kabul edilir" });

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

  try {
    // TEK ve asıl "zaten devam eden bir çeviri var mı" kontrolü:
    // queue/* ya da book/* isimli herhangi bir dal varsa, bir kitap
    // ya kuyrukta ya da işleniyordur.
    //
    // NOT: main artık HİÇ yazılmadığı için main'deki status.json'a
    // ya da input/ klasörüne bakan eski kontroller (bu dosyanın önceki
    // sürümünde vardı) artık anlamlı bir sinyal vermiyor — main'in
    // status.json'u zaten sadece bir kitap TAMAMEN bitip PR merge
    // edildiğinde güncelleniyor, süreç ortasında hiç değişmiyordu (bu,
    // bu değişiklikten ÖNCE de böyleydi, yeni bir kısıtlama değil).
    // Dal listesi kontrolü daha güvenilir: bir kitap kuyruğa girdiği
    // andan PR'ı merge edilene kadar HER an ya queue/ ya da book/
    // önekli bir dal olarak var oluyor.
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

    // main'in şu anki commit'ini al — yeni dalı ondan açacağız.
    const refRes = await gh(`/git/ref/heads/${MAIN_BRANCH}`);
    if (!refRes.ok) {
      return res.status(500).json({ error: "main dalının referansı alınamadı" });
    }
    const refData = await refRes.json();
    const mainSha = refData.object.sha;

    // queue/<slug> dalını main'in ucundan aç. main'e HİÇBİR commit
    // atılmıyor — sadece yeni bir dal referansı oluşturuluyor.
    const createRefRes = await gh("/git/refs", {
      method: "POST",
      body: JSON.stringify({ ref: `refs/heads/${queueBranch}`, sha: mainSha }),
    });
    if (!createRefRes.ok) {
      const err = await createRefRes.json();
      return res.status(500).json({ error: "Kuyruk dalı oluşturulamadı", detail: err.message });
    }

    // Dosyayı main'e DEĞİL, az önce açılan queue/<slug> dalına yaz.
    const commitRes = await gh(`/contents/input/${filename}`, {
      method: "PUT",
      body: JSON.stringify({
        message: `upload: ${filename}`,
        content: content,
        branch: queueBranch,
      }),
    });

    if (!commitRes.ok) {
      const err = await commitRes.json();
      // Yarım kalan dalı temizlemeyi dene — başarısız olsa da önemli
      // değil, bir sonraki yükleme denemesi zaten farklı bir slug
      // kullanmadıkça bu dalla çakışmaz (aynı isimli tekrar deneme
      // durumunda dal zaten var hatası alınır, kullanıcı tekrar dener).
      await gh(`/git/refs/heads/${queueBranch}`, { method: "DELETE" }).catch(() => {});
      return res.status(500).json({ error: "GitHub commit başarısız", detail: err.message });
    }

    await new Promise((r) => setTimeout(r, 2000));

    // translate.yml'i main değil, YENİ AÇILAN queue/<slug> dalıyla
    // tetikle — checkout bu ref'i kullanacak, translate.py bunun bir
    // "queue/" dalı olduğunu görüp main'e hiç dokunmadan book/<slug>'a
    // dönüştürecek (bkz. scripts/translate.py, scripts/lib/git_utils.py).
    const dispatchRes = await gh("/actions/workflows/translate.yml/dispatches", {
      method: "POST",
      body: JSON.stringify({ ref: queueBranch }),
    });

    if (!dispatchRes.ok) {
      return res.status(500).json({ error: "Workflow tetiklenemedi" });
    }

    return res.json({ success: true, filename, branch: queueBranch });
  } catch (err) {
    console.error(err);
    return res.status(500).json({ error: "Sunucu hatası" });
  }
}
