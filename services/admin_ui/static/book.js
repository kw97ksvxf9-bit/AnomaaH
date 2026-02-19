// Connect booking form to backend API
// Assumes /api_gateway/book endpoint is available and returns BookingResponse

const bookingForm = document.getElementById('bookingForm');
const estimateDiv = document.getElementById('estimate');
const confirmationDiv = document.getElementById('confirmation');
const mapDiv = document.getElementById('map');

// For demo, use stub coordinates. Replace with real map integration.
let pickupLat = 5.6037, pickupLng = -0.1870; // Accra
let dropoffLat = 5.5600, dropoffLng = -0.2050; // Accra

// Map placeholder click to set coordinates (simulate map selection)
mapDiv.onclick = function() {
  alert('Map integration coming soon! For now, using default Accra coordinates.');
};

async function updateEstimate() {
  const pickup = document.getElementById('pickup').value.trim();
  const dropoff = document.getElementById('dropoff').value.trim();
  if (pickup && dropoff) {
    // Call backend for estimate
    const payload = {
      pickup_address: pickup,
      pickup_lat: pickupLat,
      pickup_lng: pickupLng,
      dropoff_address: dropoff,
      dropoff_lat: dropoffLat,
      dropoff_lng: dropoffLng,
      phone: document.getElementById('contact').value.trim() || '0000000000',
    };
    estimateDiv.textContent = 'Calculating...';
    try {
      const r = await fetch('/api_gateway/book', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (!r.ok) throw new Error('Failed to get estimate');
      const d = await r.json();
      estimateDiv.textContent = `Estimated Fare: GHS ${d.price_ghs} | ETA: ${d.eta_min} min`;
    } catch (e) {
      estimateDiv.textContent = 'Failed to get estimate.';
    }
  } else {
    estimateDiv.textContent = '';
  }
}
document.getElementById('pickup').addEventListener('input', updateEstimate);
document.getElementById('dropoff').addEventListener('input', updateEstimate);

bookingForm.onsubmit = async function(e) {
  e.preventDefault();
  const pickup = document.getElementById('pickup').value.trim();
  const dropoff = document.getElementById('dropoff').value.trim();
  const contact = document.getElementById('contact').value.trim();
  const payment = document.getElementById('payment').value;
  const payload = {
    pickup_address: pickup,
    pickup_lat: pickupLat,
    pickup_lng: pickupLng,
    dropoff_address: dropoff,
    dropoff_lat: dropoffLat,
    dropoff_lng: dropoffLng,
    phone: contact,
    payment_method: payment
  };
  confirmationDiv.innerHTML = 'Processing...';
  try {
    const r = await fetch('/api_gateway/book', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (!r.ok) throw new Error('Booking failed');
    const d = await r.json();
    if (d.status === 'ok' && d.payment_required && d.payment_payload) {
      let payUrl = d.payment_payload.payment_url || '#';
      confirmationDiv.innerHTML = `<div class="bg-emerald-50 text-emerald-700 p-3 rounded">Booking successful!<br>Pay here: <a href="${payUrl}" class="text-sky-600 underline" target="_blank">Complete Payment</a><br>Tracking link will be sent after payment and assignment.</div>`;
    } else {
      confirmationDiv.innerHTML = '<div class="bg-rose-50 text-rose-700 p-3 rounded">Booking failed or payment unavailable.</div>';
    }
    bookingForm.reset();
    estimateDiv.textContent = '';
  } catch (e) {
    confirmationDiv.innerHTML = '<div class="bg-rose-50 text-rose-700 p-3 rounded">Booking failed. Please try again.</div>';
  }
};
