// Web3 and MetaMask helper
let userAccount = null;

async function connectMetaMask() {
    if (window.ethereum) {
        try {
            const accounts = await window.ethereum.request({ method: 'eth_requestAccounts' });
            userAccount = accounts[0];
            const btn = document.getElementById('connect-wallet-btn');
            if (btn) {
                btn.innerHTML = `<i class="bi bi-wallet2"></i> ${userAccount.substring(0, 6)}...${userAccount.substring(38)}`;
                btn.classList.remove('btn-outline-light');
                btn.classList.add('btn-warning');
            }
            
            // Sync with backend user profile if logged in
            await fetch('/api/auth/update-wallet', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ wallet_address: userAccount })
            });
            return userAccount;
        } catch (error) {
            console.error("User rejected wallet connection", error);
        }
    } else {
        alert("MetaMask not detected! Please install the MetaMask browser extension.");
    }
}

// Toast helper
function showToast(message, type = 'info') {
    const toastEl = document.getElementById('liveToast');
    if (toastEl) {
        document.getElementById('toastMessage').innerText = message;
        const toast = new bootstrap.Toast(toastEl);
        toast.show();
    } else {
        alert(message);
    }
}

