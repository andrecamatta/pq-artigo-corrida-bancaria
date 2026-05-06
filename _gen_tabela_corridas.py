"""Gera PNG com tabela comparativa de corridas sem fila."""
from pathlib import Path
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options


OUT = Path(r"C:/Users/andre/pq_projects/pq_artigo_corrida_bancaria/artigos")
HTML = OUT / "_tmp_tabela_corridas_sem_fila.html"
PNG = OUT / "tabela_corridas_sem_fila.png"


DOC = """<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<style>
  body {
    margin: 0;
    padding: 22px;
    background: #ffffff;
    font-family: "Segoe UI", Arial, sans-serif;
    color: #111827;
  }
  .figure {
    width: 1120px;
    border: 1px solid #e5e7eb;
    border-radius: 10px;
    background: #fff;
    overflow: hidden;
  }
  table {
    width: 100%;
    border-collapse: collapse;
    table-layout: fixed;
    font-size: 12.5px;
  }
  th {
    background: #ff6719;
    color: white;
    text-align: left;
    padding: 10px 12px;
    font-weight: 700;
    border-right: 1px solid rgba(255,255,255,.25);
  }
  td {
    padding: 10px 12px;
    border-top: 1px solid #e5e7eb;
    border-right: 1px solid #f3f4f6;
    vertical-align: top;
    line-height: 1.35;
  }
  tr:nth-child(even) td { background: #fafafa; }
  .case { font-weight: 700; color: #111827; }
  .year { color: #6b7280; font-size: 12px; margin-top: 2px; }
  .signal { color: #9a3412; font-weight: 650; }
  .note { color: #374151; }
</style>
</head>
<body>
<div class="figure">
  <table>
    <thead>
      <tr>
        <th style="width: 16%;">Caso</th>
        <th style="width: 21%;">Canal dominante</th>
        <th style="width: 22%;">Sinal de fragilidade</th>
        <th style="width: 18%;">Resposta</th>
        <th style="width: 23%;">Lição para liquidez</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td><div class="case">Continental Illinois</div><div class="year">EUA, 1984</div></td>
        <td>Funding atacadista, grandes depositantes não segurados, bancos correspondentes e credores institucionais sensíveis a rumores.</td>
        <td><span class="signal">Perda de cerca de 30% do funding em dez dias</span>, após dúvidas sobre a qualidade dos ativos e a capacidade de sustentar o balanço.</td>
        <td>Janela de redesconto, apoio de grandes bancos privados e assistência pública com garantia ampla.</td>
        <td>A estabilidade não depende apenas do volume total de depósitos. Depósitos grandes, não segurados e concentrados podem sair em bloco, reduzindo o horizonte de sobrevivência mesmo sem fila pública.</td>
      </tr>
      <tr>
        <td><div class="case">Northern Rock</div><div class="year">Reino Unido, 2007</div></td>
        <td>Mercados de curto prazo, securitização e investidores institucionais, antes da corrida visível de varejo.</td>
        <td>Dependência de funding atacadista para sustentar balanço alavancado em meio ao fechamento do mercado de crédito.</td>
        <td>Suporte oficial de liquidez, garantia pública aos depositantes e posterior nacionalização.</td>
        <td>O risco crítico pode estar no refinanciamento atacadista, não no comportamento inicial do varejo. Quando o mercado de curto prazo fecha, a fila nas agências apenas torna visível uma corrida que já começou.</td>
      </tr>
      <tr>
        <td><div class="case">Banco Popular</div><div class="year">Espanha, 2017</div></td>
        <td>Saída acelerada de depósitos, perda de confiança e deterioração de liquidez em poucos dias.</td>
        <td>Declaração de <em>failing or likely to fail</em> pelo BCE após a instituição deixar de cumprir exigências de liquidez.</td>
        <td>Resolução europeia, absorção de perdas por capital e venda ao Santander por um euro.</td>
        <td>Uma instituição pode entrar em resolução por falta de liquidez antes que a discussão sobre solvência esteja concluída. A métrica relevante é quanto caixa monetizável existe no prazo em que os depósitos saem.</td>
      </tr>
      <tr>
        <td><div class="case">First Republic</div><div class="year">EUA, 2023</div></td>
        <td>Clientes de alta renda, depósitos não segurados, gestão de patrimônio e confiança de mercado.</td>
        <td>Corrida de depósitos após choques de março, queda de confiança e preocupação com a base não segurada.</td>
        <td>Depósitos temporários de grandes bancos, intervenção do FDIC e venda ao JPMorgan Chase.</td>
        <td>Clientes sofisticados tratam depósitos não segurados como opção de saída imediata. Relação comercial e reputação ajudam, mas não substituem capacidade de monetizar ativos no mesmo ritmo dos saques.</td>
      </tr>
    </tbody>
  </table>
</div>
</body>
</html>
"""


def main():
    HTML.write_text(DOC, encoding="utf-8")
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1220,900")
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
