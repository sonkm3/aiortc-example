Webcam server
=============

This example illustrates how to use a raspberry pi and picamera to send h264 encoded video to the browser.
Hardware encoder built in Raspberry Pi camera module is used on this example.

Running
-------

First install the required packages:

.. code-block:: console

    $ pip install -r requirements.txt

Make sure you have installed required packges by aiortc with apt.

When you start the example, it will create an HTTP server which you
can connect to from your browser:

.. code-block:: console

    $ python rpicamera.py

You can then browse to the following page with your browser:

http://127.0.0.1:8080

Once you click `Start` the server will send video from the raspberry pi camera to the
browser.

