const url = "https://siteaiback.ownyourai.com/generate_search_terms/";
const index_name = "ownyourai";
const account = "KMS";
const project_type = "Demo";
const table_name = "Demo";
const search_model = "gpt-3.5-turbo";
const search_primer = "You will be given c.....tions, including add-ons, while keeping the language concise.";
const response_model = "gpt-4";
const response_primer = "KMS Tools - is a Cana.......ce.";

const ChatForm = document.querySelector("#ChatForm");
const ChatInput = document.querySelector("#tynChatInput");
const preChatInput = document.getElementById("preChatInput");
const preChatForm = document.getElementById("preChatForm");


async function send_req(url, text, history) {
  const requestBody = {
    query: text,
    history: history,
    index_name: index_name,
    account: account,
    project_type: project_type,
    table_name: table_name,
    search_model: search_model,
    search_primer: search_primer,
    response_model: response_model,
    response_primer: response_primer,
  };
 const response = await fetch(url, {
    headers: {
      "Content-Type": "application/json",
    },
    method: "POST",
    body: JSON.stringify(requestBody),
  });
  return response;
}

function checkForImage(text) {
  console.log("checkForImage called with text:", text);
  const image_div = document.querySelector("#ImageDiv");
  const regex = /https?:\/\/\S+\.(?:jpg|jpeg|png|tiff|svg|ico)/gi;
  const matches = text.match(regex);
  const uniqueMatches = new Set(matches);

  console.log("Checking for images in text:", text);

  if (uniqueMatches.size > 0) {
    console.log("Image URLs found:", uniqueMatches);

    uniqueMatches.forEach((match) => {
      const wrapperDiv = document.createElement("div");
      wrapperDiv.className = "tyn-reply-link has-thumb";

      const thumbDiv = document.createElement("div");
      thumbDiv.className = "tyn-reply-link-thumb";

      const link = document.createElement("a");
      link.href = match;

      const title = document.createElement("h6");
      title.className = "tyn-reply-link-title";
      title.textContent = "Header";

      const img = document.createElement("img");
      img.height = 120;
      img.src = match;
      img.alt = "";

      const anchor = document.createElement("a");
      anchor.className = "tyn-reply-anchor";
      anchor.href = match;
      anchor.textContent = match;

      link.appendChild(title);
      link.appendChild(img);
      thumbDiv.appendChild(link);
      wrapperDiv.appendChild(thumbDiv);
      wrapperDiv.appendChild(anchor);
      image_div.appendChild(wrapperDiv);
    });

    image_div.scrollIntoView();
    return true;
  }

  return false;
}

async function readAndDisplay(reader, uuid) {
  let buffer = "";
  let hasContent = false;

  while (true) {
    const { value, done } = await reader.read();
    if (done) {
      if (!hasContent) {
        document.querySelector("#" + uuid).innerHTML =
          "Sorry, I don't have any information about that.";
      }
      console.log("Calling checkForImage from readAndDisplay:", buffer);
      checkForImage(buffer);
      break;
    }
    if (value) {
      hasContent = true;
      buffer += value;
      const batch = document.querySelector("#" + uuid);
      batch.innerHTML = buffer;
      await new Promise((resolve) =>
        setTimeout(resolve, Math.floor(Math.random() * 150) + 50)
      );
    }
  }
}
async function SubmitChat() {
  const text = ChatInput.value || preChatInput.value;
  const thread = document.querySelector("#tyn-qa");
  if (text) {
    const question = `<div class="qa-item question" data-role="user">
                          <div class="avatar">
                          <div class="img">
                              <img src="/static/images/messagequestion.png" alt="">
                          </div>
                      </div>
                        <div class="">${text}</div>
                       
                    </div>`;
    thread.insertAdjacentHTML("beforeend", question);
    const questionElement = thread.lastElementChild;
    checkForImage(text, questionElement);
    const container = document.querySelector(".messages");
    if (container) {
      container.scrollTop = container.scrollHeight;
    }
    ChatInput.value = "";
    preChatInput.value = "";

    const chatItems = document.querySelectorAll(".tyn-qa-item");
    const chatHistory = Array.from(chatItems).map((item) => {
      return {
        role: item.getAttribute("data-role"),
        content: item.querySelector(".tyn-qa-message").textContent.trim(),
      };
    });

    console.log("Sending chat history:", chatHistory); // Added console.log statement
    const response = await send_req("https://siteaiback.ownyourai.com/generate_search_terms/", text, chatHistory);
    const responseBody = await response.json();
    const reader = new ReadableStream({
      start(controller) {
        let position = 0;
        const encoder = new TextEncoder();

        function enqueueNextChunk() {
          const chunk = responseBody.response.slice(position, position + 1024);
          controller.enqueue(encoder.encode(chunk));
          position += 1024;
          if (position < responseBody.response.length) {
            setTimeout(enqueueNextChunk, Math.floor(Math.random() * 150) + 50);
          } else {
            controller.close();
          }
        }

        enqueueNextChunk();
      },
    }).getReader();

    const uuid = uniqueid(16);
    const answer = `<div class="qa-item answer" data-role="assistant">
                            <div class="avatar">
                                <div class="img">
                                    <img src="/static/images/ai-icon.png" alt="">
                                </div>
                            </div>
                            <div class="">
                                <p id="${uuid}"></p>
                            </div>
                            <div class="learn-more-container">
                                <label>
                                Learn more: 
                                </label>
                                <div class="d-flex">
                                    <div class="learn-more-item">
                                    1. buildadeck.com
                                    </div>
                                    <div class="learn-more-item">
                                    2. Powertool.com
                                    </div>
                                </div>
                            </div>
                        </div>`;
    thread.insertAdjacentHTML("beforeend", answer);
    if (container) {
      container.scrollTop = container.scrollHeight;
    }

    await readAndDisplay(reader, uuid);
  }
}


ChatInput.addEventListener("keypress", async function (event) {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    await SubmitChat();
  }
});

ChatForm.addEventListener("submit", async function (event) {
  event.preventDefault();
  await SubmitChat();
});

function uniqueid(length) {
  let result = "";
  const characters =
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
  const charactersLength = characters.length;
  const initialCharacters =
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz";
  const initialCharactersLength = initialCharacters.length;
  let counter = 0;
  result += initialCharacters.charAt(
    Math.floor(Math.random() * initialCharactersLength)
  );
  counter += 1;
  while (counter < length) {
    result += characters.charAt(Math.floor(Math.random() * charactersLength));
    counter += 1;
  }
  return result;
}



// ---- PRE CHAT --- //

window.addEventListener("message", (event) => {
  const payload = event.data;
  const postStep = document.getElementById("post-step");
  if (payload["eventType"] === "getHeight" && !payload["close"]) {
    if (postStep.style.display === "flex") {
      window.parent.postMessage({ height: "650px", state: "post" }, "*");
    } else {
      window.parent.postMessage({ height: "58px", state: "pre" }, "*");
      preChatInput.style.height = `auto`; // set new height based on content
      preChatInput.style.overflowY = "hidden"; // disable scrolling when content fits within four rows
    }
  } else {
    if (postStep.style.display === "none") {
      return;
    }else{
      window.parent.postMessage({ height: "58px", state: "pre" }, "*");
      const preStep = document.getElementById("pre-step");
      preStep.style.display = "block";
      const postStep = document.getElementById("post-step");
      postStep.style.display = "none";
      preChatInput.style.height = `auto`; // set new height based on content
      preChatInput.style.overflowY = "hidden"; // disable scrolling when content fits within four rows
    }
  }
});

function toggleStep() {
  const preStep = document.getElementById("pre-step");
  preStep.style.display = "none";
  const postStep = document.getElementById("post-step");
  postStep.style.display = "flex";
  window.parent.postMessage({ height: "650px", state: "post" }, "*");
  ChatInput.focus();
}

preChatInput.addEventListener("keypress", async function (event) {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    toggleStep();
    await SubmitChat();
  }
});

preChatForm.addEventListener("submit", async function (event) {
  event.preventDefault();
  toggleStep();
  await SubmitChat();
});

// DOTS SCROLL CODE

const imagesListContainer = document.querySelector(".topImagesWrapper");
const imagesList = document.querySelector(".topImages");
const imageItems = document.querySelectorAll(".imageContainer");
const dotsContainer = document.querySelector(".dots-container");

const maxVisibleItems = 3;
let numDots = Math.ceil(imageItems.length / maxVisibleItems);

// Dynamically create the dots
for (let i = 0; i < numDots; i++) {
  const dot = document.createElement("div");
  dot.classList.add("dot");
  if (i === 0) {
    dot.classList.add("active");
  }
  dot.addEventListener("click", function () {
    // Scroll to the corresponding product item
    const imageIndex = i * maxVisibleItems;
    const imageItem = imageItems[imageIndex];
    const imageItemOffset = imageItem.offsetLeft - imagesList.offsetLeft;
    imagesList.scrollTo({
      left: imageItemOffset,
      behavior: "smooth",
    });
  });
  dotsContainer.appendChild(dot);
}

// Update the dot classes based on the scroll position
imagesList.addEventListener("scroll", function () {
  const scrollLeft = imagesList.scrollLeft;
  const visibleImages = Math.floor(
    imagesListContainer.offsetWidth / imageItems[0].offsetWidth
  );
  const lastImageIndex = imageItems.length - 1;
  const maxScrollLeft = imagesList.scrollWidth - imagesList.offsetWidth;
  const isLastImageInViewport =
    scrollLeft >= maxScrollLeft - imageItems[lastImageIndex].offsetWidth;
  let currentDotIndex = Math.floor(
    scrollLeft / (visibleImages * imageItems[0].offsetWidth)
  );
  if (isLastImageInViewport) {
    currentDotIndex = numDots - 1; // Set index to the last dot
  }
  const currentDot = document.querySelectorAll(".dot")[currentDotIndex];

  // Remove active class from all dots
  const activeDot = document.querySelector(".dot.active");
  activeDot.classList.remove("active");
  // Set active class to the current dot
  currentDot.classList.add("active");
});

// AUTO SCALLING OF TEXT AREA.

const preStep = document.getElementById("pre-step");

preChatInput.addEventListener("input", () => {
  preChatInput.style.height = "auto"; // reset height to allow for re-calculation
  if (preChatInput.scrollHeight > preChatInput.clientHeight * 4) {
    preChatInput.style.height = `${preChatInput.clientHeight * 4}px`;
    preChatInput.style.overflowY = "scroll"; // enable scrolling when content exceeds four rows
  } else {
    preChatInput.style.height = `${preChatInput.scrollHeight}px`; // set new height based on content
    preChatInput.style.overflowY = "hidden"; // disable scrolling when content fits within four rows
  }
  window.parent.postMessage(
    { height: `${preStep.offsetHeight}px`, state: "pre" },
    "*"
  );
});

preChatInput.addEventListener("keydown", (event) => {
  // shrink textarea when backspace key is pressed and content fits within one row
  if (
    event.key === "Backspace" &&
    preChatInput.scrollHeight <= preChatInput.clientHeight
  ) {
    preChatInput.style.height = "0";
    setTimeout(() => (preChatInput.style.height = "auto"), 0);
    window.parent.postMessage(
      { height: `${preStep.offsetHeight}px`, state: "pre" },
      "*"
    );
  }
});
