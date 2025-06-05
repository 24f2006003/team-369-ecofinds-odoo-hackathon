// Google Sign-In functionality
function initGoogleSignIn() {
    google.accounts.id.initialize({
        client_id: document.getElementById('google-client-id').value,
        callback: handleGoogleSignIn,
        auto_select: false,
        cancel_on_tap_outside: true,
        context: 'signin',
        ux_mode: 'popup',
        flow: 'implicit',
        origin: window.location.origin,
        prompt_parent_id: 'google-signin-button'
    });
    
    google.accounts.id.renderButton(
        document.getElementById('google-signin-button'),
        { 
            theme: 'outline', 
            size: 'large', 
            width: '100%',
            text: 'signin_with',
            shape: 'rectangular',
            logo_alignment: 'left',
            type: 'standard'
        }
    );
}

function handleGoogleSignIn(response) {
    // Send the token to your backend
    fetch('/auth/google-signin', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            credential: response.credential
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            window.location.href = data.redirect_url;
        } else {
            console.error('Google sign-in failed:', data.error);
            alert('Google sign-in failed: ' + data.error);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('An error occurred during Google sign-in');
    });
}

// Initialize Google Sign-In when the page loads
document.addEventListener('DOMContentLoaded', initGoogleSignIn); 