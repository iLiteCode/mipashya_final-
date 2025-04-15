
//dark mode toggle buttonJavaScript

  // JavaScript to handle theme persistence
  document.addEventListener('DOMContentLoaded', () => {
    const checkbox = document.getElementById('theme-toggle');
    const body = document.body;

    // Check if there's a saved theme preference
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark') {
      checkbox.checked = true;
      body.classList.remove('light');
      body.classList.add('dark');
    } else {
      body.classList.remove('dark');
      body.classList.add('light');
    }

    // Toggle theme on checkbox change
    checkbox.addEventListener('change', () => {
      if (checkbox.checked) {
        body.classList.remove('light');
        body.classList.add('dark');
        localStorage.setItem('theme', 'dark');
      } else {
        body.classList.remove('dark');
        body.classList.add('light');
        localStorage.setItem('theme', 'light');
      }
    });
  });



//dark mode toggle buttonJavaScript







// Unified JavaScript
 function cancelAd(adId) {
    const adElement = document.getElementById(adId);
    if (adElement) {
        adElement.style.display = 'none';
    }
  }
  
  function showAds() {
    const upperAds = document.querySelectorAll('.advertisements-upper-menu .advertisement');
    const footerAds = document.querySelectorAll('.advertisements-below-footer .advertisement');
    
    // Function to handle single ad display (constant until manually closed)
    function handleSingleAd(ad, containerClass) {
        ad.style.display = 'block';
        // No auto-close timeout; stays until manually closed
    }
  
    // Function to handle multiple ad rotation (5-second intervals)
    function handleMultipleAds(ads, containerClass) {
        let currentAdIndex = 0;
  
        function showNextAd() {
            ads.forEach(ad => ad.style.display = 'none');
            if (currentAdIndex < ads.length) {
                ads[currentAdIndex].style.display = 'block';
                currentAdIndex++;
            } else {
                currentAdIndex = 0;
            }
        }
  
        showNextAd();
        return setInterval(showNextAd, 5000);
    }
  
    // Handle upper menu ads
    if (upperAds.length > 1) {
        handleMultipleAds(upperAds, 'advertisements-upper-menu');
    } else if (upperAds.length === 1) {
        handleSingleAd(upperAds[0], 'advertisements-upper-menu');
    }
  
    // Handle footer ads
    if (footerAds.length > 1) {
        handleMultipleAds(footerAds, 'advertisements-below-footer');
    } else if (footerAds.length === 1) {
        handleSingleAd(footerAds[0], 'advertisements-below-footer');
    }
  }
  
  // Start the ad rotation when page loads 
  window.onload = showAds;