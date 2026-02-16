
var superSportsCarIcon = L.icon({
  iconUrl: 'data:image/svg+xml;base64,' + btoa(`
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 32" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <path d="M2 22h60l-12-14H18l-16 14z" fill="#e10600"/>
      <path d="M20 8h22l4 10H20z" fill="#e0e0e0"/>
      <circle cx="18" cy="26" r="6" fill="black"/>
      <circle cx="46" cy="26" r="6" fill="black"/>
      <circle cx="18" cy="26" r="3" fill="gray"/>
      <circle cx="46" cy="26" r="3" fill="gray"/>
      <path d="M10 10l-6 4" stroke="#ff0000" stroke-width="1.5"/>
      <path d="M54 10l6 4" stroke="#ff0000" stroke-width="1.5"/>
    </svg>
  `),
  iconSize: [40, 20],
  iconAnchor: [20, 10],
  popupAnchor: [0, -10]
});


// ==========================
// Tähti-ikoni
// ==========================

var starIcon = L.icon({
  iconUrl: 'data:image/svg+xml;base64,' + btoa(`
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="#FFD700">
      <path d="M12 2l3 7 7 .5-5 5 1.5 7L12 18l-6.5 3.5L7 14 2 9.5 9 9z"/>
    </svg>
  `),
  iconSize: [30, 30],
  iconAnchor: [15, 15]
});


// Green pin icon for saved routes
var favoriteIcon = L.icon({
    iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-green.png',
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
    shadowSize: [41, 41]
});