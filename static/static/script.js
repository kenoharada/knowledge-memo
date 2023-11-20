let timeoutId;
let fileName;

// タブを開く関数
function openContent(evt, contentName) {
  // すべてのタブコンテンツを非表示にする
  var i, tabcontent, tablinks;
  tabcontent = document.getElementsByClassName("tabcontent");
  for (i = 0; i < tabcontent.length; i++) {
    tabcontent[i].style.display = "none";
  }
  // すべてのタブボタンのactiveクラスを削除する
  tablinks = document.getElementsByClassName("tablinks");
  for (i = 0; i < tablinks.length; i++) {
    tablinks[i].className = tablinks[i].className.replace(" active", "");
  }
  // 選択されたタブコンテンツを表示し、ボタンにactiveクラスを追加する
  document.getElementById(contentName).style.display = "block";
  evt.currentTarget.className += " active";
}

// URLから動画IDを抽出する関数
function extractVideoId(url) {
  const urlObj = new URL(url);
  return urlObj.searchParams.get("v");
}

// メモ入力時のイベントリスナー
document.getElementById("memoInput").addEventListener("input", function () {
  clearTimeout(timeoutId);
  timeoutId = setTimeout(() => {
    saveMemo();
  }, 3000); // 3秒後に保存
});

// メモ入力欄からフォーカスが外れた時のイベントリスナー
document.getElementById("memoInput").addEventListener("blur", saveMemo);

// メモ保存ボタンのイベントリスナー
document.getElementById("saveMemoButton").addEventListener("click", saveMemo);

// 動画処理ボタンのイベントリスナー
document.getElementById("processButton").addEventListener("click", function () {
  const videoUrl = document.getElementById("videoUrlInput").value;
  const videoId = extractVideoId(videoUrl);
  if (videoId) {
    displayVideo(videoId);
    fetchSummary(videoId); // 動画処理ボタンを押したら要約を取得する
    fileName = videoId;
  } else {
    alert("正しいYouTubeのビデオURLを入力してください。");
  }
});

// 動画を表示する関数
function displayVideo(videoId) {
  const videoContainer = document.getElementById("mediaContainer");
  videoContainer.innerHTML = `<iframe width="560" height="315" src="https://www.youtube.com/embed/${videoId}" frameborder="0" allowfullscreen></iframe>`;
}

// メモを保存する関数
function saveMemo() {
  const memo = document.getElementById("memoInput").value;

  if (fileName) {
    fetch(`/save_memo?file_name=${fileName}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ memo: memo }),
    })
      .then((response) => response.json())
      .then((data) => console.log(data.message))
      .catch((error) => console.error("Error:", error));
  }
}

// 動画の要約を取得する関数
function fetchSummary(videoId) {
  fetch(`/process_video?video_id=${videoId}`)
    .then((response) => {
      if (!response.ok) {
        throw new Error("Network response was not ok");
      }
      return response.json();
    })
    .then((data) => {
      const summaryElement = document.getElementById("summary");
      const subtitlesElement = document.getElementById("subtitles");

      summaryElement.innerHTML = "";
      subtitlesElement.innerHTML = "";

      data.summary.split("\n").forEach((line) => {
        summaryElement.appendChild(document.createTextNode(line));
        summaryElement.appendChild(document.createElement("br"));
      });

      data.subtitles.split("\n").forEach((line) => {
        subtitlesElement.appendChild(document.createTextNode(line));
        subtitlesElement.appendChild(document.createElement("br"));
      });
    })
    .catch((error) => {
      console.error("Error:", error);
    });
}

// ドラッグ＆ドロップ及びファイル選択イベントリスナー
const fileDropArea = document.getElementById("fileDropArea");
const fileInput = document.getElementById("fileInput");

fileDropArea.addEventListener("click", () => fileInput.click());

fileInput.addEventListener("change", function (event) {
  const files = event.target.files;
  if (files.length > 0) {
    displayMedia(files[0]); // メディアを表示
    processMedia(files[0]); // メディアを処理
  }
});

fileDropArea.addEventListener("dragover", function (event) {
  event.preventDefault();
  fileDropArea.classList.add("active");
});

fileDropArea.addEventListener("dragleave", function (event) {
  fileDropArea.classList.remove("active");
});

fileDropArea.addEventListener("drop", function (event) {
  event.preventDefault();
  fileDropArea.classList.remove("active");
  const files = event.dataTransfer.files;
  if (files.length > 0) {
    displayMedia(files[0]); // メディアを表示
    processMedia(files[0]); // メディアを処理
  }
});

// ドラッグ＆ドロップされたメディアファイルを表示する関数
function displayMedia(file) {
  const mediaContainer = document.getElementById("mediaContainer");
  mediaContainer.innerHTML = ""; // Clear the container
  const mediaElement = document.createElement(
    file.type.startsWith("video/") ? "video" : "audio"
  );
  mediaElement.src = URL.createObjectURL(file);
  mediaElement.controls = true;
  mediaElement.autoplay = true;
  // Add styles directly to the video element
  // mediaElement.style.width = "100%";
  // mediaElement.style.height = "100%";
  mediaElement.style.objectFit = "cover"; // Apply object-fit to the video element
  mediaContainer.appendChild(mediaElement);
}

// ドラッグ＆ドロップされたメディアファイルを処理する関数
function processMedia(file) {
  const formData = new FormData();
  formData.append("file", file);
  // 拡張子なしのファイル名を取得
  fileName = file.name.split(".")[0];
  console.log(fileName);

  fetch("/process_media", {
    method: "POST",
    body: formData,
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.summary) {
        const summaryElement = document.getElementById("summary");
        const subtitlesElement = document.getElementById("subtitles");

        summaryElement.innerHTML = "";
        subtitlesElement.innerHTML = "";

        data.summary.split("\n").forEach((line) => {
          summaryElement.appendChild(document.createTextNode(line));
          summaryElement.appendChild(document.createElement("br"));
        });

        data.subtitles.split("\n").forEach((line) => {
          subtitlesElement.appendChild(document.createTextNode(line));
          subtitlesElement.appendChild(document.createElement("br"));
        });
      }
    })
    .catch((error) => console.error("エラー:", error));
}
