"""Gera o diagrama do jogo de corrida bancária em PNG."""
from pathlib import Path
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options


OUT = Path(r"C:/Users/andre/pq_projects/pq_artigo_corrida_bancaria/artigos")
HTML = OUT / "_tmp_diagrama_nash.html"
PNG = OUT / "diagrama_nash_pareto_corrida.png"


DOC = r"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<style>
  body {
    margin: 0;
    padding: 24px;
    background: #ffffff;
    font-family: "Segoe UI", Arial, sans-serif;
    color: #111827;
  }
  .figure {
    width: 1040px;
    border: 1px solid #e5e7eb;
    border-radius: 10px;
    background: #fff;
    padding: 24px 26px 20px;
    box-sizing: border-box;
  }
  .title {
    font-size: 22px;
    font-weight: 700;
    margin: 0 0 4px;
  }
  .subtitle {
    font-size: 14px;
    color: #4b5563;
    margin: 0 0 20px;
  }
  .layout {
    display: grid;
    grid-template-columns: 130px 1fr;
    gap: 16px;
    align-items: center;
  }
  .row-label {
    writing-mode: vertical-rl;
    transform: rotate(180deg);
    font-size: 13px;
    color: #374151;
    text-align: center;
    letter-spacing: .02em;
  }
  .matrix-wrap {
    display: grid;
    grid-template-columns: 130px 1fr 1fr;
    grid-template-rows: 44px 1fr 1fr;
    gap: 8px;
  }
  .corner { }
  .axis {
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 13px;
    color: #374151;
    font-weight: 600;
  }
  .choice {
    background: #f9fafb;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    min-height: 122px;
    display: flex;
    align-items: center;
    justify-content: center;
    text-align: center;
    padding: 12px;
    box-sizing: border-box;
  }
  .label {
    background: #f3f4f6;
    border-color: #d1d5db;
    color: #374151;
    font-weight: 700;
    min-height: 122px;
  }
  .good {
    background: #ecfdf5;
    border-color: #10b981;
  }
  .bad {
    background: #fff7ed;
    border-color: #ff6719;
  }
  .mixed {
    background: #f9fafb;
    border-color: #d1d5db;
  }
  .cell-title {
    font-size: 18px;
    font-weight: 750;
    margin-bottom: 7px;
  }
  .cell-sub {
    font-size: 13px;
    color: #374151;
    line-height: 1.35;
  }
  .tag {
    display: inline-block;
    margin-top: 9px;
    padding: 3px 8px;
    border-radius: 999px;
    font-size: 12px;
    font-weight: 700;
  }
  .tag-good {
    color: #065f46;
    background: #d1fae5;
  }
  .tag-bad {
    color: #9a3412;
    background: #fed7aa;
  }
  .legend {
    margin-top: 18px;
    display: flex;
    gap: 18px;
    font-size: 13px;
    color: #374151;
  }
  .dot {
    display: inline-block;
    width: 10px;
    height: 10px;
    border-radius: 50%;
    margin-right: 6px;
    vertical-align: -1px;
  }
  .green { background: #10b981; }
  .orange { background: #ff6719; }
  .gray { background: #9ca3af; }
</style>
</head>
<body>
  <div class="figure">
    <div class="title">Dois equilíbrios, uma ordem de Pareto</div>
    <div class="subtitle">Jogo simplificado entre depositantes pacientes sob restrição de atendimento por ordem de chegada</div>
    <div class="layout">
      <div class="row-label">Depositante A</div>
      <div class="matrix-wrap">
        <div class="corner"></div>
        <div class="axis">Depositante B: esperar</div>
        <div class="axis">Depositante B: sacar cedo</div>

        <div class="choice label">Depositante A:<br>esperar</div>
        <div class="choice good">
          <div>
            <div class="cell-title">(Esperar, esperar)</div>
            <div class="cell-sub">O banco preserva os ativos longos.<br>Ambos recebem o consumo prometido em t = 2.</div>
            <span class="tag tag-good">Nash Pareto-superior</span>
          </div>
        </div>
        <div class="choice mixed">
          <div>
            <div class="cell-title">(Esperar, sacar)</div>
            <div class="cell-sub">Quem espera fica exposto à fila.<br>O incentivo individual muda.</div>
          </div>
        </div>

        <div class="choice label">Depositante A:<br>sacar cedo</div>
        <div class="choice mixed">
          <div>
            <div class="cell-title">(Sacar, esperar)</div>
            <div class="cell-sub">Quem saca primeiro se protege.<br>Quem espera absorve o risco residual.</div>
          </div>
        </div>
        <div class="choice bad">
          <div>
            <div class="cell-title">(Sacar, sacar)</div>
            <div class="cell-sub">A corrida força liquidação prematura.<br>O seguro de liquidez é destruído.</div>
            <span class="tag tag-bad">Nash Pareto-inferior</span>
          </div>
        </div>
      </div>
    </div>
    <div class="legend">
      <span><span class="dot green"></span>Coordenação preserva liquidez</span>
      <span><span class="dot orange"></span>Coordenação produz corrida</span>
      <span><span class="dot gray"></span>Desvios individuais criam incentivo para correr</span>
    </div>
  </div>
</body>
</html>
"""


def main():
    HTML.write_text(DOC, encoding="utf-8")
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1150,900")
    options.add_argument("--force-device-scale-factor=2")
    driver = webdriver.Chrome(options=options)
    try:
        driver.get(f"file:///{HTML.as_posix()}")
        time.sleep(0.4)
        elem = driver.find_element("class name", "figure")
        elem.screenshot(str(PNG))
        print(f"Saved {PNG}")
    finally:
        driver.quit()
        HTML.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
