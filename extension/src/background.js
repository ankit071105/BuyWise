// Background service worker — handles periodic checks and notifications

chrome.runtime.onInstalled.addListener(() => {
  console.log('BuyWise extension installed')
})

// Listen for price drop notifications from backend polling
// ⚠️ NOTE: For real push notifications, integrate with your backend webhook
// and use chrome.notifications.create() here
chrome.runtime.onMessage.addListener((msg) => {
  if (msg.type === 'PRICE_DROP') {
    chrome.notifications.create({
      type: 'basic',
      iconUrl: '../icons/icon48.png',
      title: '🔥 BuyWise Price Drop Alert!',
      message: `${msg.productName}: Price dropped to ₹${msg.newPrice.toLocaleString('en-IN')}!`,
      priority: 2
    })
  }
})
