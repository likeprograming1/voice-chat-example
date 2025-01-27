### **1. WebSocket이 필요한 이유**
WebRTC 자체에는 클라이언트 간 연결 정보를 교환할 방법이 포함되어 있지 않습니다. 따라서 클라이언트들이 다음 정보를 교환할 방법이 필요합니다:
- **SDP (Session Description Protocol)**: Offer/Answer로 P2P 연결 초기화 정보 포함.
- **ICE Candidate**: 클라이언트의 네트워크 정보(IP 주소, 포트 등).

이 정보를 WebSocket을 사용해 클라이언트 간 교환합니다. 서버는 데이터를 단순히 전달만 하고, WebRTC 연결 자체에는 관여하지 않습니다.

---

### **2. 클라이언트 역할 (RTC 연결 설정)**
WebSocket을 통해 신호 교환이 끝나면, 클라이언트가 WebRTC 연결을 직접 설정합니다. 과정은 다음과 같습니다:

1. **RTCPeerConnection 객체 생성**  
   클라이언트 단에서 WebRTC 연결을 생성합니다:
   ```javascript
   const peerConnection = new RTCPeerConnection({
       iceServers: [
           { urls: "stun:stun.l.google.com:19302" }, // STUN 서버 (필수)
           { urls: "turn:your-turn-server.com", username: "user", credential: "pass" } // TURN 서버 (옵션)
       ]
   });
   ```

2. **로컬 스트림 추가**  
   마이크나 카메라의 미디어 데이터를 WebRTC 연결에 추가합니다:
   ```javascript
   const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
   stream.getTracks().forEach(track => peerConnection.addTrack(track, stream));
   ```

3. **SDP Offer 생성 및 전송**  
   P2P 연결을 시작하려는 클라이언트가 Offer를 생성해 WebSocket을 통해 다른 클라이언트에게 전송합니다:
   ```javascript
   const offer = await peerConnection.createOffer();
   await peerConnection.setLocalDescription(offer);
   signalingServer.send(JSON.stringify(peerConnection.localDescription));
   ```

4. **SDP Answer 처리**  
   다른 클라이언트가 Offer를 받고, 이에 대한 Answer를 생성해 WebSocket으로 다시 전송합니다:
   ```javascript
   signalingServer.onmessage = async (event) => {
       const message = JSON.parse(event.data);
       if (message.type === "offer") {
           await peerConnection.setRemoteDescription(new RTCSessionDescription(message));
           const answer = await peerConnection.createAnswer();
           await peerConnection.setLocalDescription(answer);
           signalingServer.send(JSON.stringify(peerConnection.localDescription));
       } else if (message.type === "answer") {
           await peerConnection.setRemoteDescription(new RTCSessionDescription(message));
       }
   };
   ```

5. **ICE Candidate 교환**  
   WebRTC가 P2P 연결을 설정하는 데 필요한 ICE Candidate 정보를 자동으로 생성합니다. 이를 WebSocket을 통해 교환합니다:
   ```javascript
   peerConnection.onicecandidate = (event) => {
       if (event.candidate) {
           signalingServer.send(JSON.stringify({ type: "candidate", candidate: event.candidate }));
       }
   };

   signalingServer.onmessage = async (event) => {
       const message = JSON.parse(event.data);
       if (message.type === "candidate") {
           await peerConnection.addIceCandidate(new RTCIceCandidate(message.candidate));
       }
   };
   ```

6. **원격 스트림 처리**  
   P2P 연결이 성공하면, 다른 클라이언트에서 보낸 오디오 데이터를 수신합니다:
   ```javascript
   peerConnection.ontrack = (event) => {
       const remoteAudio = document.getElementById("remote-audio");
       remoteAudio.srcObject = event.streams[0];
   };
   ```

---

### **3. 전체 흐름 요약**
1. **WebSocket 연결**: 서버를 통해 클라이언트 간 신호 교환(Signaling).
2. **SDP Offer/Answer 교환**: WebRTC 연결 설정에 필요한 초기 정보 교환.
3. **ICE Candidate 교환**: P2P 연결을 설정하기 위한 네트워크 정보 교환.
4. **WebRTC P2P 연결**: 두 클라이언트가 직접 연결해 음성/영상 데이터를 교환.

---

### **4. 서버와 클라이언트의 책임**
| 역할                | WebSocket (FastAPI 서버)              | WebRTC (클라이언트)              |
|--------------------|------------------------------------|--------------------------------|
| **목적**           | 신호 교환(Signaling)               | 실제 P2P 연결 설정 및 데이터 전송 |
| **작동 방식**       | Offer/Answer, ICE Candidate 전달  | 로컬/원격 SDP 및 Candidate 처리  |
| **데이터 처리**     | 중계(클라이언트 간 전달)           | 멀티미디어 데이터 송수신          |
| **연결 종료 시**    | 클라이언트 제거                    | P2P 연결 닫기                    |

---

### **5. 결론**
- 서버는 클라이언트 간 신호(Signaling) 교환만 처리합니다.
- 클라이언트는 WebRTC를 통해 직접 P2P 연결을 설정하고, 음성 데이터를 전송합니다.

이 구조에서는 서버가 단순히 "중계자" 역할만 하기 때문에 성능에 큰 영향을 주지 않으면서, 클라이언트 간 P2P 통신을 효율적으로 설정할 수 있습니다. 😊
