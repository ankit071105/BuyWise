// ⚠️ CHANGE THIS: Update to your backend URL
const API_BASE = 'http://localhost:8000'

// State
let token = null
let currentProductUrl = null
let currentProductId = null

async function apiCall(path, method = 'GET', body = null) {
  const opts = {
    method,
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` }
  }
  if (body) opts.body = JSON.stringify(body)
  const res = await fetch(`${API_BASE}${path}`, opts)
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

function showError(msg) {
  const el = document.getElementById('error-msg')
  el.textContent = msg
  el.style.display = 'block'
}

function setScoreStyle(score) {
  const el = document.getElementById('ext-score')
  el.className = 'score-ring'
  if (score >= 7.5) el.classList.add('score-great')
  else if (score >= 5.5) el.classList.add('score-consider')
  else if (score >= 4.0) el.classList.add('score-wait')
  else el.classList.add('score-avoid')
}

async function analyzeProduct(url) {
  document.getElementById('loading').style.display = 'block'
  document.getElementById('score-section').style.display = 'none'
  try {
    const result = await apiCall('/api/products/analyze', 'POST', { url })
    document.getElementById('loading').style.display = 'none'
    if (result.success) {
      currentProductId = result.product_id
      const score = result.buy_score?.score
      document.getElementById('ext-score').textContent = score?.toFixed(1) || '—'
      setScoreStyle(score || 0)
      document.getElementById('ext-reasoning').textContent = result.llm_reasoning || result.buy_score?.reasoning || 'Analysis complete.'
      document.getElementById('score-section').style.display = 'block'
    }
  } catch (e) {
    document.getElementById('loading').style.display = 'none'
    showError('Analysis failed. Is BuyWise backend running?')
  }
}

// On popup open
chrome.storage.local.get(['buywise_token', 'buywise_user'], async (data) => {
  token = data.buywise_token

  if (!token) {
    document.getElementById('auth-section').style.display = 'block'
    return
  }

  document.getElementById('auth-section').style.display = 'none'
  document.getElementById('main-section').style.display = 'block'

  // Get current tab URL
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true })
  const url = tab?.url || ''
  const isSupported = url.includes('amazon.in') || url.includes('flipkart.com')

  document.getElementById('status-dot').className = `dot ${isSupported ? '' : 'inactive'}`
  document.getElementById('status-text').textContent = isSupported
    ? 'Product page detected!'
    : 'Visit Amazon or Flipkart to auto-analyze'

  if (isSupported) {
    currentProductUrl = url
    const platform = url.includes('amazon') ? 'Amazon' : 'Flipkart'
    document.getElementById('ext-platform').textContent = platform
    document.getElementById('product-detected').style.display = 'block'

    // Get product info from content script
    chrome.tabs.sendMessage(tab.id, { type: 'GET_PRODUCT_INFO' }, (info) => {
      if (info?.name) document.getElementById('ext-product-name').textContent = info.name
      if (info?.price) document.getElementById('ext-product-price').textContent = `₹${info.price.toLocaleString('en-IN')}`
    })

    // Auto-analyze
    analyzeProduct(url)
  }
})

// Login
document.getElementById('ext-login-btn').addEventListener('click', async () => {
  const email = document.getElementById('ext-email').value
  const password = document.getElementById('ext-password').value
  if (!email || !password) return showError('Enter email and password')

  try {
    const body = new URLSearchParams({ username: email, password })
    const res = await fetch(`${API_BASE}/api/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body
    })
    if (!res.ok) throw new Error('Invalid credentials')
    const data = await res.json()
    chrome.storage.local.set({ buywise_token: data.access_token, buywise_user: data.user })
    location.reload()
  } catch (e) {
    showError(e.message || 'Login failed')
  }
})

// Track product
document.getElementById('ext-track-btn').addEventListener('click', async () => {
  if (!currentProductId) return
  try {
    await apiCall('/api/products/track', 'POST', { product_id: currentProductId })
    document.getElementById('ext-track-btn').textContent = '✅ Tracked!'
  } catch { showError('Tracking failed') }
})

// Manual analyze
document.getElementById('manual-analyze-btn').addEventListener('click', async () => {
  const url = document.getElementById('manual-url').value.trim()
  if (!url) return
  document.getElementById('product-detected').style.display = 'block'
  document.getElementById('ext-product-name').textContent = 'Analyzing...'
  await analyzeProduct(url)
})

// Logout
document.getElementById('logout').addEventListener('click', () => {
  chrome.storage.local.remove(['buywise_token', 'buywise_user'])
  location.reload()
})
