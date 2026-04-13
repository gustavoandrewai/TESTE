export type ChartAsset = { title: string; imageUrl: string; caption: string };

function svgDataUri(title: string, values: number[], color = "#2563eb") {
  const width = 560;
  const height = 180;
  const max = Math.max(...values);
  const min = Math.min(...values);
  const points = values
    .map((v, i) => {
      const x = 40 + i * ((width - 80) / (values.length - 1));
      const y = height - 30 - ((v - min) / (max - min || 1)) * (height - 60);
      return `${x},${y}`;
    })
    .join(" ");

  const svg = `<svg xmlns='http://www.w3.org/2000/svg' width='${width}' height='${height}'>
  <rect width='100%' height='100%' fill='white'/>
  <text x='20' y='22' font-family='Arial' font-size='14' fill='#0f172a'>${title}</text>
  <polyline fill='none' stroke='${color}' stroke-width='3' points='${points}' />
  </svg>`;
  return `data:image/svg+xml;utf8,${encodeURIComponent(svg)}`;
}

export function generateMockCharts(): ChartAsset[] {
  return [
    {
      title: "US 10Y Yield (mock)",
      imageUrl: svgDataUri("US 10Y Yield", [4.12, 4.18, 4.22, 4.19, 4.25], "#7c3aed"),
      caption: "Abertura de yields mantém sensibilidade de duration e growth assets."
    },
    {
      title: "DXY (mock)",
      imageUrl: svgDataUri("DXY", [103.1, 103.4, 103.7, 103.6, 103.9], "#ea580c"),
      caption: "Força do dólar pressiona moedas emergentes e condições financeiras."
    }
  ];
}
