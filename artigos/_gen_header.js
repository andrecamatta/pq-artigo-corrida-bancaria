const fs = require("fs");
const { execFileSync } = require("child_process");
const path = require("path");

const OUT_DIR = "C:/Users/andre/pq_projects/pq_artigo_corrida_bancaria/artigos";
const ARTICLE_HTML = path.join(OUT_DIR, "corrida-bancaria-diamond-dybvig-regulacao.html");
const HEADER_PNG = path.join(OUT_DIR, "corrida-bancaria-diamond-dybvig-regulacao_header.png");
const META_JSON = path.join(OUT_DIR, "corrida-bancaria-diamond-dybvig-regulacao_header.meta.json");
const PAYLOAD = path.join(OUT_DIR, "_payload_header.json");
const RESPONSE = path.join(OUT_DIR, "_response_header.json");
const KEY_FILE = "C:/Users/andre/.claude/commands/openrouter.key";

const html = fs.readFileSync(ARTICLE_HTML, "utf8");
const text = html
  .replace(/<style[\s\S]*?<\/style>/gi, " ")
  .replace(/<[^>]*>/g, " ")
  .replace(/\s+/g, " ")
  .trim()
  .slice(0, 9000);

const prompt = `Create a 1536x1024 landscape header image for a technical Substack article about bank runs, Diamond-Dybvig, liquidity buffers, deposit insurance, and regulation after fast digital runs.

Absolute constraints:
- No text, no letters, no numbers, no logos, no watermarks.
- No people, no literal bank facade, no money bills, no clichéd panic crowd.
- Clean professional finance/research aesthetic, suitable for Pilulas de Quant.
- Predominant orange #FF6719 over a dark graphite background, with secondary cyan/blue and off-white accents.
- Abstract data-visualization composition, not a poster with readable labels.

Central visual metaphor — domino cascade:
- The dominant motif is a long curving row of thin vertical bars (abstract domino tiles) traversing the composition.
- The first tiles on the left stand upright; toward the middle they begin tilting and falling forward in a clear cascade; on the right side the tiles are already toppled, lying flat in an orange streak.
- The cascade is geometric and minimal — each tile is a clean rectangular bar, slightly translucent, with subtle shadow. No realism, no game pieces, no literal domino dots.
- The toppled tiles glow in saturated orange #FF6719; the standing tiles remain dark graphite with thin off-white edges; tiles mid-fall transition through orange tones.
- Speed is implied by motion blur on the falling tiles and by a faint trajectory arc.

Supporting elements (secondary, do not overpower the cascade):
- Behind the dominoes, a faint dark liquidity network of nodes and thin lines, suggesting interconnected balance sheets.
- A translucent buffer ring around the area where the cascade started, partially depleted, suggesting HQLA/LCR under stress.
- A subtle game-theory payoff grid motif in the background, abstract and unreadable.
- A few orange flow lines in the background drifting away from the cascade epicenter.

Mood:
- Tension, coordination failure, speed, and self-excitation — the dominoes embody how one withdrawal triggers the next in a digital bank run (Hawkes-style cascade).
- Restrained, professional, suitable for a quantitative finance audience.

Avoid:
- Literal cartoon dominoes with dots, board-game pieces, or playful tile graphics.
- Realistic bank branches, crowds, banknotes, coins, hands, phones as the main subject.
- Any text-like glyphs, labels, equations, tickers, or numbers.
- Purple-dominant palettes, beige editorial palettes, or generic AI gradients.

Article context:
${text}`;

const payload = {
  model: "google/gemini-3.1-flash-image-preview",
  messages: [{ role: "user", content: prompt }],
};

fs.writeFileSync(PAYLOAD, JSON.stringify(payload));

const key = fs.readFileSync(KEY_FILE, "utf8").trim();
console.log("Calling OpenRouter image model...");
execFileSync("curl.exe", [
  "-sS",
  "--max-time",
  "180",
  "https://openrouter.ai/api/v1/chat/completions",
  "-H",
  `Authorization: Bearer ${key}`,
  "-H",
  "Content-Type: application/json",
  "-d",
  `@${PAYLOAD}`,
  "-o",
  RESPONSE,
], { stdio: "inherit" });

const data = JSON.parse(fs.readFileSync(RESPONSE, "utf8"));
const imageUrl = data?.choices?.[0]?.message?.images?.[0]?.image_url?.url;
if (!imageUrl) {
  console.error("No image returned. Response preview:");
  console.error(JSON.stringify(data, null, 2).slice(0, 3000));
  process.exit(1);
}

const match = imageUrl.match(/data:image\/([^;]+);base64,(.+)/s);
if (!match) {
  console.error("Image URL was not a base64 data URI.");
  process.exit(1);
}

const buf = Buffer.from(match[2], "base64");
fs.writeFileSync(HEADER_PNG, buf);
fs.writeFileSync(META_JSON, JSON.stringify({
  model: payload.model,
  treatment: "abstract domino cascade as central motif, faint liquidity network behind, depleted buffer ring at cascade origin, orange #FF6719 over graphite, no text",
  bytes: buf.length,
}, null, 2));

fs.rmSync(PAYLOAD, { force: true });
fs.rmSync(RESPONSE, { force: true });
console.log(`Saved ${HEADER_PNG} (${(buf.length / 1024).toFixed(1)} KB)`);
