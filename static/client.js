
// -----------------------signatures----------------------------------
function generateSignature(timestamp, data = "", token) {
  
  if (!timestamp || !token) { 
      console.error("Missing timestamp or token for signature generation");
      return null;
  }
  const message = `${timestamp}.${data || ""}`;
  console.log("Message:", message);
  return CryptoJS.HmacSHA256(message, token).toString(CryptoJS.enc.Hex);
}


// -----------------------API Request----------------------------------
function apiRequest(url, method, data = null) {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open(method, url, true);
    
    xhr.setRequestHeader("Content-Type", "application/json");
    const email = localStorage.getItem("email");
    const token = localStorage.getItem("token");
    
    const timestamp = Math.floor(Date.now() / 1000).toString();
    xhr.setRequestHeader("email", email);
    xhr.setRequestHeader("Timestamp", timestamp);

    let requestData = "";
    if (data && (method === "POST" || method === "PUT")) {
        requestData = JSON.stringify(data);
    }
    
    const signature = generateSignature(timestamp, requestData, token);
    if (signature) {
        xhr.setRequestHeader("Signature", signature);
    }
    
    xhr.onload = function () {
      try {
        const jsonResponse = JSON.parse(xhr.responseText);
        if (xhr.status >= 200 && xhr.status < 300) {
          resolve(jsonResponse);
        } else {
          reject({
            status: xhr.status,
            message: jsonResponse.message
          });
        }
      } catch (e) {
        reject({
          status: xhr.status,
          message: "Invalid response from server"
        });
      }
    };
    
    xhr.onerror = function () {
      reject({
        status: 0,
        message: "Network error"
      });
    };
    xhr.send(requestData);
    
  });
}

// -----------------------User Friendly Message----------------------------------
function getUserFriendlyMessage(error) {
  const defaultMessages = {
    400: "Please check your input and try again.",
    401: "Authentication failed. Please log in again.",
    404: "The requested resource was not found.",
    409: "There was a conflict with the current state.",
    500: "Something went wrong on our end. Please try again later."
  };

  if (error.status === 401 && error.message === "Wrong password") {
    return "The password you entered is incorrect. Please try again.";
  } else if (error.status === 401 && error.message === "Invalid token") {
    return "Your session has expired. Please log in again.";
  } else if (error.status === 404 && error.message === "Email not registered") {
    return "This email is not registered in our system. Please check or sign up.";
  } else if (error.status === 409 && error.message === "Email already registered") {
    return "This email is already registered. Please use a different email or log in.";
  }
  
  return defaultMessages[error.status] || "An unexpected error occurred.";
}
  
// ----------------------- Utility Functions----------------------------------
function showAlert(message, isSuccess = false) {
    let alertBox = document.getElementById("alert");
    if (!alertBox) {
      alertBox = document.createElement("div");
      alertBox.id = "alert";
      document.body.appendChild(alertBox);
    }
    alertBox.style.backgroundColor = isSuccess ? "#4CAF50" : "#FF4444";
    alertBox.style.color = "#fff";
    alertBox.innerText = message;
    alertBox.classList.add("show");
    alertBox.style.display = "block";
    setTimeout(() => {
      alertBox.classList.remove("show");
      setTimeout(() => (alertBox.style.display = "none"), 500);
    }, 3000);
  }
  
function validateEmail(email) {
    const emailRegex = /\S+@\S+\.\S+/;
    return emailRegex.test(email);
    
}


function validatePassword(password) {
    return password.length >= 8;
  }
  
function validatePasswordMatch(password, confirmPassword) {
    return password === confirmPassword;
  }
  

// -----------------------View Functions---------------------------------- 
function displayDefaultView() {
    const token = localStorage.getItem("token");
    if (token) {
      displayView("profileview");
    } else {
      displayView("welcomeview");
    }
  }
  
function displayView(viewId) {
    const mainContainer = document.getElementById("mainContainer");
    
    if (viewId === "welcomeview") {
      const source = document.getElementById("welcomeview-template").innerHTML;
      const template = Handlebars.compile(source);
      mainContainer.innerHTML = template();
      
      handleLoginForm();
      handleSignupForm();
    } else {
      const viewContent = document.getElementById(viewId)?.innerHTML;
      if (!viewContent) {
        console.error(`Element with ID ${viewId} does not exist.`);
        return;
      }
      mainContainer.innerHTML = viewContent;
    
      if (viewId === "profileview") {
        initializeTabs();
        setupLogoutButton();
        changePassword();
        getUserData();
        postMessage();
        enableDragAndDrop();
        getMessages();
        findUserByEmail();
        postMessageByBrowser();
        getMessagesByBrowser();
      }
    }
  }

// -----------------------Tab Function----------------------------------
function initializeTabs() {
    const tabs = document.querySelectorAll(".tab");
    const panels = document.querySelectorAll(".panel");
  
    const defaultTab = document.querySelector('.tab[data-target="homePanel"]');
    if (defaultTab) defaultTab.classList.add("active");
    const defaultPanel = document.getElementById("homePanel");
    if (defaultPanel) defaultPanel.classList.add("active");
  
    tabs.forEach(tab => {
      tab.addEventListener("click", function () {
        tabs.forEach(t => t.classList.remove("active"));
        this.classList.add("active");
        panels.forEach(panel => panel.classList.remove("active"));
        const targetPanel = document.getElementById(this.getAttribute("data-target"));
        if (targetPanel) targetPanel.classList.add("active");
      });
    });
  }
  
 
// -----------------------Log in----------------------------------
function handleLoginForm() {
    const loginForm = document.getElementById("loginForm");
    loginForm.onsubmit = async function (event) {
      event.preventDefault();
      const email = document.getElementById("loginUsername").value;
      const password = document.getElementById("loginPassword").value;
      const data = { username: email, password: password };
  
      try {
        const response = await apiRequest("http://127.0.0.1:8000/sign_in", "POST", data);
        console.log("Login response:", response);
        localStorage.setItem("token", response.data);
        localStorage.setItem("email", email);
        console.log("Token stored in localStorage.");
        establishWebSocketConnection(response.data);
        displayView("profileview");
        showAlert("login successful", true);
        
      } catch (error) {
        console.error("Login error:", error);
        showAlert(getUserFriendlyMessage(error));
      }
    };
  }


// -----------------------Websocket----------------------------------
function establishWebSocketConnection(token) {
    const ws = new WebSocket(`ws://127.0.0.1:8000/ws`);

    ws.onopen = () => {
      console.log("WebSocket connected.");
      ws.send(token); // Send the token once the connection is open
      console.log("Token sent to server.");
    };

    ws.onmessage = (event) => {
        if (event.data === "logout") {
            console.log("Logged out from another session.");
            showAlert("You have been logged out from another session.");
            localStorage.removeItem("token");
            displayView("welcomeview"); 
            ws.close(); // Close the connection after logout
        }
    };
    ws.onerror = (error) => {
        console.error("WebSocket Error:", error);
        ws.close(); // Close connection on error
    };

    return ws;
}


// -----------------------Signup----------------------------------
function handleSignupForm() {
    const signupForm = document.getElementById("signupForm");
    signupForm.onsubmit = async function (event) {
      event.preventDefault();
  
      const email = document.getElementById("signupEmail").value;
      const password = document.getElementById("signupPassword").value;
      const confirmPassword = document.getElementById("signupPasswordRepeat").value;
  
      if (!validateEmail(email)) {
        showAlert("Invalid email format");
        return;
      }
      if (!validatePassword(password)) {
        showAlert("Password must be at least 8 characters long");
        return;
      }
      if (!validatePasswordMatch(password, confirmPassword)) {
        showAlert("Passwords do not match");
        return;
      }
  
      const userData = {
        email: email,
        password: password,
        firstname: document.getElementById("signupFirstname").value,
        familyname: document.getElementById("signupSurname").value,
        gender: document.getElementById("signupGender").value,
        city: document.getElementById("signupCity").value,
        country: document.getElementById("signupCountry").value,
      };
  
      try {
        const response = await apiRequest("http://127.0.0.1:8000/sign_up", "POST", userData);
          showAlert("Signup successful! Please log in.", true);
          displayView("welcomeview");
          showAlert("Signup successful! Please log in.", true);
        
      } catch (error) {
        console.error("Signup error:", error);
        showAlert(getUserFriendlyMessage(error));
      }
    };
  }
  

// -----------------------Logout----------------------------------
function setupLogoutButton() {
    const logoutButton = document.getElementById("logoutButton");
    logoutButton.addEventListener("click", async function () {
      const token = localStorage.getItem("token");
      if (token) {
        try {
          response = await apiRequest("http://127.0.0.1:8000/sign_out", "DELETE");
          console.log("Logout response:", response);
          localStorage.removeItem("token");
          localStorage.removeItem("email");
          displayView("welcomeview");
          showAlert("Logout successful", true);
        } catch (error) {
          console.error("Logout error:", error);

              showAlert(getUserFriendlyMessage(error));
          
          
        }
      }
    });
  }
  

// -----------------------Change Password----------------------------------
function changePassword() {
    const changePasswordButton = document.getElementById("changePasswordButton");
    if (!changePasswordButton.dataset.listenerAdded) {
      changePasswordButton.dataset.listenerAdded = "true";
      changePasswordButton.addEventListener("click", async function () {
        const oldPassword = document.getElementById("oldPassword").value;
        const newPassword = document.getElementById("newPassword").value;
        const confirmPassword = document.getElementById("confirmPassword").value;
        const token = localStorage.getItem("token");
  
        if (!validatePassword(newPassword)) {
          showAlert("Password must be at least 8 characters long");
          return;
        }
        if (!validatePasswordMatch(newPassword, confirmPassword)) {
          showAlert("Passwords do not match.");
          return;
        }
  
        const data = { oldpassword: oldPassword, newpassword: newPassword };
        try {
          const response = await apiRequest("http://127.0.0.1:8000/change_password", "PUT", data);
          showAlert("Password changed successfully!", true);
          document.getElementById("oldPassword").value = "";
          document.getElementById("newPassword").value = "";
          document.getElementById("confirmPassword").value = "";

        } catch (error) {
          console.error("Change password error:", error);
          showAlert(getUserFriendlyMessage(error));
        }
      });
    }
  }
  
// -----------------------User Data----------------------------------
async function getUserData() {
    try {
      const response = await apiRequest("http://127.0.0.1:8000/get_user_data_by_token", "GET");
      document.getElementById("userFirstName").innerText = response.data.firstname;
      document.getElementById("userLastName").innerText = response.data.lastname;
      document.getElementById("userGender").innerText = response.data.gender;
      document.getElementById("userEmail").innerText = response.data.email;
      document.getElementById("userCity").innerText = response.data.city;
      document.getElementById("userCountry").innerText = response.data.country;
      
    } catch (error) {
      console.error("User data error:", error);
      showAlert(getUserFriendlyMessage(error));
      
    }
  }

// -----------------------Post Message----------------------------------
function postMessage() {
    const postMessageButton = document.getElementById("postMessageButton");
    if (!postMessageButton.dataset.listenerAdded) {
      postMessageButton.dataset.listenerAdded = "true";
      postMessageButton.addEventListener("click", async function () {
        const token = localStorage.getItem("token");
        const message = document.getElementById("messageInput").value;
        if (message.trim() === "") {
          showAlert("Message cannot be empty.");
          return;
        }
        try {
            email = localStorage.getItem("email");
            const response = await apiRequest("http://127.0.0.1:8000/post_message", "POST", { message: message, email: email, reciver: email });
            showAlert("Message posted successfully!", true);
            document.getElementById("messageInput").value
        } catch (error) {
          console.error("Post message error:", error);
          showAlert(getUserFriendlyMessage(error));
      }
      });
    }
  }

  
// -----------------------Get Messages----------------------------------
function getMessages() {
    const reloadMessageButton = document.getElementById("reloadMessageButton");
    if (!reloadMessageButton.dataset.listenerAdded) {
        reloadMessageButton.dataset.listenerAdded = "true";
        reloadMessageButton.addEventListener("click", async function () {
            try {
                const response = await apiRequest("http://127.0.0.1:8000/get_user_messages_by_token", "GET");
                const messageFeed = document.getElementById("messageFeed");
                messageFeed.innerHTML = "";

                response.data.forEach((msg, index) => {
                    const messageElement = document.createElement("div");
                    messageElement.classList.add("message");
                    messageElement.textContent = msg.post;
                    messageElement.setAttribute("draggable", "true"); // Enable drag
                    messageElement.setAttribute("id", "msg" + index); // Unique ID
                    messageElement.addEventListener("dragstart", handleDragStart);
                    messageFeed.appendChild(messageElement);
                });

            } catch (error) {
                console.error("Get messages error:", error);
                showAlert(getUserFriendlyMessage(error));
            }
        });
    }
}

// -----------------------Drag and Drop----------------------------------
function handleDragStart(event) {
    event.dataTransfer.setData("text", event.target.textContent);
}

function allowDrop(event) {
    event.preventDefault();
}

function handleDrop(event) {
    event.preventDefault();
    const droppedText = event.dataTransfer.getData("text");
    if (droppedText.includes(":")) {
      modifeddroppedText = droppedText.substring(droppedText.indexOf(":") + 1).trim();
    }
    document.getElementById("messageInput").value = modifeddroppedText;
   
}

function enableDragAndDrop() {
    const messageInput = document.getElementById("messageInput");
    messageInput.addEventListener("dragover", allowDrop);
    messageInput.addEventListener("drop", handleDrop);
}

// -----------------------Find User By Email----------------------------------
function findUserByEmail() {
    const findUserButton = document.getElementById("browseButton");
    findUserButton.addEventListener("click", async function () {
      const token = localStorage.getItem("token");
      const email = document.getElementById("browseEmail").value;
      if (email.trim() === "") {
        showAlert("Please enter an email address");
        return;
      }
      try {
        const response = await apiRequest("http://127.0.0.1:8000/get_user_data_by_email/" + encodeURIComponent(email), "GET");
          document.getElementById("browseFirstName").innerText = response.data.firstname;
          document.getElementById("browseLastName").innerText = response.data.lastname;
          document.getElementById("browseGender").innerText = response.data.gender;
          document.getElementById("browseEmailDisplay").innerText = response.data.email;
          document.getElementById("browseCity").innerText = response.data.city;
          document.getElementById("browseCountry").innerText = response.data.country;
      } catch (error) {
        console.error("Find user error:", error);
      
      if (error.status === 401) {
          showAlert("User not found");
      }
      else{  
          showAlert(getUserFriendlyMessage(error));
      }
    }
    });
  }

// -----------------------Post Message By Browser----------------------------------
function postMessageByBrowser() {
    const postMessageButtonBrowser = document.getElementById("postMessageButtonBrowser");
    postMessageButtonBrowser.addEventListener("click", async function () {
      const token = localStorage.getItem("token");
      const message = document.getElementById("messageInputBrowser").value;
      const toEmail = document.getElementById("browseEmail").value;
      if (toEmail.trim() === "" || message.trim() === "") {
        showAlert("Please enter both an email address and a message");
        return;
      }
      
      try {
        const userdata = await apiRequest("http://127.0.0.1:8000/get_user_data_by_token", "GET");
        email = userdata.data.email;
        const response = await apiRequest("http://127.0.0.1:8000/post_message", "POST", { message: message, email: toEmail, reciver: email });
        showAlert("Message posted successfully!", true);
        document.getElementById("messageInputBrowser").value = "";
      } catch (error) {
        console.error("Post message by browser error:", error);    
            showAlert(getUserFriendlyMessage(error));
      }
    });
  }

  
// -----------------------Get Messages By Browser----------------------------------
function getMessagesByBrowser() {
    const reloadMessageButtonBrowser = document.getElementById("reloadMessageButtonBrowser");
    reloadMessageButtonBrowser.addEventListener("click", async function () {
      const email = document.getElementById("browseEmail").value;
      if (email.trim() === "") {
        showAlert("Please enter an email address");
        return;
      }
      try {
        const response = await apiRequest("http://127.0.0.1:8000/get_user_messages_by_email/" + encodeURIComponent(email), "GET");
          const messageFeed = document.getElementById("messageFeedBrowser");
          messageFeed.innerHTML = "";
          response.data.forEach(msg => {
            const messageElement = document.createElement("div");
            messageElement.classList.add("message");
            messageElement.textContent = msg.post;
            messageFeed.appendChild(messageElement);
          });
      } catch (error) {
        console.error("Get messages by browser error:", error);
            showAlert(getUserFriendlyMessage(error));
      }
    });
  }
  
// -----------------------Event Listener----------------------------------
document.addEventListener("DOMContentLoaded", function () {
    displayDefaultView();
  });
  