export const config = { maxDuration: 10 };

// Site durumu:
//  - Aktif kitap: HÂLÂ ÇEVRİLEN book/<slug> dalındaki status.json (çeviri
//    veya review bitmemiş). Ara ilerleme main'e hiç yazılmıyor, main'deki
//    status.json sadece EN SON MERGE EDİLEN kitabın durumu — eskiden burada
//    yalnızca o okunduğu için site çeviri sırasında hep eski kitabı
//    gösteriyordu.
//  - Çevirisi+review'u bitmiş kitaplar "aktif" SAYILMAZ; kuyruk onları
//    beklemez. İki aşama: `finishing` (QA/düzeltme/ciltleme sürüyor) ve
//    `awaiting_merge` (PR açık, inceleme bekliyor). Çevrilen kitap ve sıra
//    yoksa bunlardan biri (indirme bağlantılarıyla) gösterilir.
//  - Hiçbiri yoksa: main'deki status.json (son merge edilen kitap).
//  - Sıra: yükleme sırasına göre bekleyen queue/<slug> dalları (dosyası
//    gerçekten yüklenmiş olanlar — yarım kalmış yüklemelerin yetim dalları
//    sayılmaz).
export default async function handler(req, res) {
  if (req.method !== "GET")
    return res.status(405).json({ error: "Method not allowed" });

  const REPO = process.env.GH_REPO;
  const TOKEN = process.env.GH_PAT;
  const MAIN_BRANCH = process.env.GH_BRANCH || "main";

  if (!REPO || !TOKEN)
    return res.status(500).json({ error: "Sunucu yapılandırması eksik" });

  const gh = (path) =>
    fetch(`https://api.github.com/repos/${REPO}${path}`, {
      headers: { Authorization: `token ${TOKEN}` },
    });

  async function readStatus(ref) {
    const r = await gh(`/contents/status.json?ref=${encodeURIComponent(ref)}`);
    if (!r.ok) return null;
    const data = await r.json();
    try {
      return JSON.parse(Buffer.from(data.content, "base64").toString());
    } catch {
      return null;
    }
  }

  try {
    const branchesRes = await gh("/branches?per_page=100");
    const names = branchesRes.ok ? (await branchesRes.json()).map((b) => b.name) : [];

    const bookInfos = await Promise.all(
      names
        .filter((n) => n.startsWith("book/"))
        .map(async (name) => ({ name, st: await readStatus(name) }))
    );
    // Groq fazı (çeviri + review) bitti mi?
    const groqDone = (b) => b.st && b.st.status === "completed" && b.st.review_status === "completed";
    const inProgress = bookInfos.find((b) => !groqDone(b)) || null;
    const finishing = bookInfos.filter((b) => groqDone(b) && b.st.convert_status !== "completed");
    const awaiting = bookInfos.filter((b) => groqDone(b) && b.st.convert_status === "completed");
    const activeBranch = inProgress ? inProgress.name : null;

    const queueInfos = await Promise.all(
      names
        .filter((n) => n.startsWith("queue/"))
        .map(async (name) => {
          const r = await gh(`/compare/${MAIN_BRANCH}...${name}`);
          if (!r.ok) return null;
          const d = await r.json();
          if (!(d.ahead_by > 0)) return null;
          return {
            branch: name,
            slug: name.slice("queue/".length),
            queued_at: d.commits?.[0]?.commit?.committer?.date || "",
          };
        })
    );
    const queue = queueInfos
      .filter(Boolean)
      .sort((a, b) =>
        a.queued_at === b.queued_at
          ? a.slug.localeCompare(b.slug)
          : a.queued_at < b.queued_at
          ? -1
          : 1
      )
      .map((q, i) => ({ ...q, position: i + 1 }));

    let status;
    let displayBranch = null;
    if (inProgress) {
      // Dal yeni açıldıysa status.json henüz olmayabilir.
      status =
        inProgress.st ||
        { status: "running", book: inProgress.name.slice("book/".length) };
      displayBranch = inProgress.name;
    } else if (queue.length > 0) {
      // Aktif kitap yok ama sırada bekleyen var: biri anında başlayacak,
      // main'deki eski (tamamlanmış) kitabı göstermek karışıklık yaratır.
      status = { status: "idle" };
    } else if (finishing.length > 0) {
      status = finishing[0].st;
      displayBranch = finishing[0].name;
    } else if (awaiting.length > 0) {
      status = awaiting[0].st;
      displayBranch = awaiting[0].name;
    } else {
      status = (await readStatus(MAIN_BRANCH)) || { status: "idle" };
    }

    let outputFiles = [];
    let epubFile = null;

    if (status.status === "completed" && status.book) {
      const ref = displayBranch || MAIN_BRANCH;
      const outputRes = await gh(
        `/contents/output/${status.book}?ref=${encodeURIComponent(ref)}`
      );
      if (outputRes.ok) {
        const files = await outputRes.json();

        // txt files
        outputFiles = files
          .filter((f) => f.name.endsWith(".txt"))
          .map((f) => ({ name: f.name, download_url: f.download_url }));

        // epub output (built by convert.py)
        const epubEntry = files.find((f) => f.name.endsWith("_tr.epub"));
        if (epubEntry) {
          epubFile = { name: epubEntry.name, download_url: epubEntry.download_url };
        }
      }
    }

    return res.json({
      ...status,
      outputFiles,
      epubFile,
      queue,
      active_branch: activeBranch,
      finishing: finishing.map((b) => b.name.slice("book/".length)),
      awaiting_merge: awaiting.map((b) => b.name.slice("book/".length)),
    });
  } catch (err) {
    console.error(err);
    return res.status(500).json({ error: "Sunucu hatası" });
  }
}
