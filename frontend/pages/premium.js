export default function Premium() {
  async function goPremium() {
    const res = await fetch(process.env.NEXT_PUBLIC_API_URL + "/create-checkout-session", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email: "test@example.com" })
    });
    const data = await res.json();
    window.location = data.checkout_url;
  }

  return (
    <div>
      <h1>Hazte Premium</h1>
      <button onClick={goPremium}>Suscribirme 5,99€/mes</button>
    </div>
  )
}
