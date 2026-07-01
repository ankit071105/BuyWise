// Content script — runs on Amazon/Flipkart product pages
// Extracts product info and injects BuyWise badge

function extractProductInfo() {
  const url = window.location.href

  if (url.includes('amazon')) {
    const name = document.getElementById('productTitle')?.textContent?.trim()
    const priceEl = document.querySelector('.a-price-whole')
    const price = priceEl ? parseFloat(priceEl.textContent.replace(/,/g, '').replace('.', '')) : null
    return { name, price, platform: 'amazon', url }
  }

  if (url.includes('flipkart')) {
    const name = document.querySelector('.VU-ZEz, .B_NuCI')?.textContent?.trim()
    const priceEl = document.querySelector('._30jeq3, .Nx9bqj')
    const price = priceEl ? parseFloat(priceEl.textContent.replace('₹', '').replace(/,/g, '')) : null
    return { name, price, platform: 'flipkart', url }
  }

  return null
}

// Listen for popup requesting product info
chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.type === 'GET_PRODUCT_INFO') {
    sendResponse(extractProductInfo())
  }
})
