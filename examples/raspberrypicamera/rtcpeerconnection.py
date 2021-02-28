from rtcrtpsender import RTCRtpSender

from aiortc import RTCPeerConnection as OriginalRTCPeerConnection
from aiortc.rtcrtpparameters import RTCRtpSendParameters
from aiortc.rtcrtpreceiver import RTCRtpReceiver
from aiortc.rtcrtptransceiver import RTCRtpTransceiver


class RTCPeerConnection(OriginalRTCPeerConnection):
    def __createTransceiver(
        self, direction: str, kind: str, sender_track=None
    ) -> RTCRtpTransceiver:
        dtlsTransport = self.__createDtlsTransport()
        transceiver = RTCRtpTransceiver(
            direction=direction,
            kind=kind,
            sender=RTCRtpSender(sender_track or kind, dtlsTransport),
            receiver=RTCRtpReceiver(kind, dtlsTransport),
        )
        transceiver.receiver._set_rtcp_ssrc(transceiver.sender._ssrc)
        transceiver.sender._stream_id = self.__stream_id
        transceiver._bundled = False
        transceiver._transport = dtlsTransport
        self.__transceivers.append(transceiver)
        return transceiver

    def __localRtp(self, transceiver: RTCRtpTransceiver) -> RTCRtpSendParameters:
        codecs = []
        if (
            transceiver._preferred_codecs is not None
            and len(transceiver._preferred_codecs) > 0
        ):
            for pref in transceiver._preferred_codecs:
                for codec in transceiver._codecs:
                    if codec.mimeType.lower() == pref.mimeType.lower():
                        codecs.append(codec)
        else:
            codecs = transceiver._codecs
        rtp = RTCRtpSendParameters(
            codecs=codecs,
            headerExtensions=transceiver._headerExtensions,
            muxId=transceiver.mid,
        )
        rtp.rtcp.cname = self.__cname
        rtp.rtcp.ssrc = transceiver.sender._ssrc
        rtp.rtcp.mux = True
        return rtp
