let timeoutId;

// URLから動画IDを抽出する関数
function extractVideoId(url) {
  const urlObj = new URL(url);
  const videoId = urlObj.searchParams.get("v");
  return videoId;
}

document.getElementById("memoInput").addEventListener("input", function () {
  clearTimeout(timeoutId);
  timeoutId = setTimeout(() => {
    saveMemo();
  }, 3000); // 3秒後に保存
});

document.getElementById("memoInput").addEventListener("blur", saveMemo);

document.getElementById("saveMemoButton").addEventListener("click", saveMemo);

document.getElementById("processButton").addEventListener("click", function () {
  const videoUrl = document.getElementById("videoUrlInput").value;
  const videoId = extractVideoId(videoUrl);
  if (videoId) {
    displayVideo(videoId);
    fetchSummary(videoId); // 動画処理ボタンを押したら要約を取得する
  }
});

function displayVideo(videoId) {
  const videoContainer = document.getElementById("videoContainer");
  videoContainer.innerHTML = `<iframe width="560" height="315" src="https://www.youtube.com/embed/${videoId}" frameborder="0" allowfullscreen></iframe>`;
}

function saveMemo() {
  const memo = document.getElementById("memoInput").value;
  const videoUrl = document.getElementById("videoUrlInput").value;
  const videoId = videoUrl.split("v=")[1];

  if (videoId) {
    fetch(`/save_memo?video_id=${videoId}`, {
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
      // 既存の内容をクリア
      summaryElement.innerHTML = "";

      // 改行で分割し、各行を個別のテキストノードとして追加
      data.summary.split("\n").forEach((line) => {
        if (line) {
          summaryElement.appendChild(document.createTextNode(line));
        }
        summaryElement.appendChild(document.createElement("br"));
      });
    })
    .catch((error) => {
      console.error("Error:", error);
    });
}
