import asyncio
import json
import cv2
import numpy as np
from aiortc import RTCPeerConnection, RTCSessionDescription
import aiohttp
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WebRTCClient:
    def __init__(self, server_url):
        self.server_url = server_url
        self.pc = None
        self.video_track = None
        self.frame_queue = asyncio.Queue(maxsize=30)
       
    async def connect(self):
        self.pc = RTCPeerConnection()

        # ✅ Add transceiver to fix media direction error
        self.pc.addTransceiver("video", direction="recvonly")

        @self.pc.on("track")
        def on_track(track):
            logger.info(f"Receiving {track.kind} track")
            if track.kind == "video":
                self.video_track = track
                asyncio.create_task(self.process_video_track())

        @self.pc.on("connectionstatechange")
        async def on_connectionstatechange():
            logger.info(f"Connection state: {self.pc.connectionState}")

        await self.pc.setLocalDescription(await self.pc.createOffer())

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.server_url}/offer",
                json={
                    "sdp": self.pc.localDescription.sdp,
                    "type": self.pc.localDescription.type
                }
            ) as response:
                answer_data = await response.json()
                answer = RTCSessionDescription(
                    sdp=answer_data["sdp"],
                    type=answer_data["type"]
                )
                await self.pc.setRemoteDescription(answer)

        logger.info("WebRTC connection established")

    async def process_video_track(self):
        while True:
            try:
                frame = await self.video_track.recv()
                img = frame.to_ndarray(format="bgr24")

                if self.frame_queue.full():
                    try:
                        self.frame_queue.get_nowait()
                    except:
                        pass
                await self.frame_queue.put(img)

            except Exception as e:
                logger.error(f"Error receiving frame: {e}")
                break

    async def display_loop(self):
        cv2.namedWindow("WebRTC Stream", cv2.WINDOW_NORMAL)
        frame_count = 0
        fps_time = datetime.now()

        while True:
            try:
                frame = await asyncio.wait_for(self.frame_queue.get(), timeout=1.0)

                frame_count += 1
                if frame_count % 30 == 0:
                    elapsed = (datetime.now() - fps_time).total_seconds()
                    fps = 30 / elapsed
                    fps_time = datetime.now()
                    cv2.putText(frame, f"FPS: {fps:.1f}", (10, 30),
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

                cv2.imshow("WebRTC Stream", frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

            except asyncio.TimeoutError:
                logger.warning("No frames received for 1 second")
                continue
            except Exception as e:
                logger.error(f"Display error: {e}")
                break

        cv2.destroyAllWindows()

    async def run(self):
        await self.connect()
        await self.display_loop()
        if self.pc:
            await self.pc.close()

async def main():
    server_url = "http://192.168.16.101:8080"  # Adjust to your Raspberry Pi's IP
    client = WebRTCClient(server_url)

    try:
        await client.run()
    except KeyboardInterrupt:
        logger.info("Shutting down...")

if __name__ == "__main__":
    print("WebRTC Client for receiving Raspberry Pi camera stream")
    print("Press 'q' in video window to quit")
    print("-" * 50)
    asyncio.run(main())
