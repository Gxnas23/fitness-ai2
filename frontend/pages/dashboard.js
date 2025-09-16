import { useState } from "react";

export default function Dashboard() {
  const [calorias, setCalorias] = useState(null);

  async function getPredict() {
    const res = await fetch(process.env.NEXT_PUBLIC_API_URL + "/predict", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ age: 30, sex: "M", weight: 75, height: 180 })
    });
    const data = await res.json();
    setCalorias(data.calorias_mantenimiento);
  }

  return (
    <div>
      <h1>Dashboard</h1>
      <button onClick={getPredict}>Calcular calorías gratis</button>
      {calorias && <p>Calorías de mantenimiento: {calorias}</p>}
      <a href="/premium">Hazte Premium</a>
    </div>
  )
}
