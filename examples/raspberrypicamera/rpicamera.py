import asyncio
import json
import logging
import os
from collections import OrderedDict


import av
import picamera
from aiohttp import web
from pitrack import H264EncodedStreamTrack
from rtcpeerconnection import RTCPeerConnection
from rtcrtpsender import RTCRtpSender

from aiortc import RTCSessionDescription
from aiortc.contrib.media import MediaPlayer
from aiortc.rtcrtpparameters import RTCRtpCodecCapability

logger = logging.getLogger(__name__)

FRAME_RATE = 30
CAMERA_RESOLUTION = (640, 480)
BASE_PATH = os.path.dirname(__file__)

audio = None
camera = None

audio_capabilities = RTCRtpSender.getCapabilities("audio")

codec_parameters = OrderedDict(
    [
        ("packetization-mode", "1"),
        ("level-asymmetry-allowed", "1"),
        ("profile-level-id", "42001f"),
    ]
)
pi_capability = RTCRtpCodecCapability(
    mimeType="video/H264", clockRate=90000, channels=None, parameters=codec_parameters
)
preferences = [pi_capability]
pcs = set()


async def index(request):
    content = open(os.path.join(BASE_PATH, "index.html"), "r").read()
    return web.Response(content_type="text/html", text=content)


async def javascript(request):
    content = open(os.path.join(BASE_PATH, "client.js"), "r").read()
    return web.Response(content_type="application/javascript", text=content)


async def offer(request):
    global audio, camera
    params = await request.json()
    offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])

    video_track = H264EncodedStreamTrack(FRAME_RATE)
    if not camera:
        camera = picamera.PiCamera()
        camera.resolution = CAMERA_RESOLUTION
        camera.framerate = FRAME_RATE
    else:
        camera.stop_recording()

    camera.start_recording(
        video_track,
        format="h264",
        profile="constrained",
        inline_headers=True,
        sei=False,
    )

    audio = MediaPlayer("hw:1,0", format='alsa', options={'channels': '1'})

    pc = RTCPeerConnection()
    pcs.add(pc)

    @pc.on("iceconnectionstatechange")
    async def on_iceconnectionstatechange():
        print("ICE connection state is %s" % pc.iceConnectionState)
        if pc.iceConnectionState == "failed":
            await pc.close()
            pcs.discard(pc)

    await pc.setRemoteDescription(offer)
    for t in pc.getTransceivers():
        if t.kind == "audio" and audio:
            t.setCodecPreferences(audio_capabilities.codecs)
            pc.addTrack(audio.audio)
        if t.kind == "video":
            t.setCodecPreferences(preferences)
            pc.addTrack(video_track)
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)
    logger.info(answer)
    return web.Response(
        content_type="application/json",
        text=json.dumps(
            {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}
        ),
    )


async def on_shutdown(app):
    global camera
    # close peer connections
    print("Shutting down")
    coros = [pc.close() for pc in pcs]
    await asyncio.gather(*coros)
    pcs.clear()
    camera.stop_recording()
    camera.close()
    audio.close()


if __name__ == "__main__":
    ssl_context = None
    app = web.Application()
    app.on_shutdown.append(on_shutdown)
    app.router.add_get("/", index)
    app.router.add_get("/client.js", javascript)
    app.router.add_post("/offer", offer)
    web.run_app(app, host="0.0.0.0", port=8080, ssl_context=ssl_context)
