from threading import Thread, Event

WAITING = 0
COMPLETE = 1
DISCONNECTED = 2
FAILED = 3

class CameraResult:
  def __init__(self):
    self.scan = None
    self.code = WAITING
    self.message = ''

class CameraThread:

  def __init__(self):
    self.thread = Thread(target=self.loop)
    self.thread.daemon = True
    self.captureEvent = Event()
    self.camera = None
    self.resultEvent = Event()
    self.result = CameraResult()
    self.shouldRefocus = True

  def start(self):
    self.thread.start()

  def loop(self):
    while True:
      self.waitToCapture()

      result = CameraResult()
      refocusGood = True
      prepareGood = self.camera.prepare()
      if prepareGood:
        if self.shouldRefocus:
          refocusGood = self.camera.refocus()
        if not refocusGood:
          result.scan = None
          result.message = 'Failed to refocus: ' + self.camera.message
          result.code = FAILED
          if not self.camera.is_connected():
            result.code = DISCONNECTED
        else:
          scan = self.camera.capture()
          if scan is None:
            result.scan = None
            result.message = 'Failed to capture: ' + self.camera.message
            result.code = FAILED
            if not self.camera.is_connected():
              result.code = DISCONNECTED
          else:
            result.scan = scan
            result.message = ''
            result.code = COMPLETE
      else:
        result.scan = None
        result.message = 'Failed to prepare camera: ' + self.camera.message
        result.code = FAILED
        if not self.camera.is_connected():
          result.code = DISCONNECTED
      self.setResult(result)

  # Interface for outside to trigger capture and get the result
  def beginCapture(self, camera, shouldRefocus):
    self.camera = camera
    self.shouldRefocus = shouldRefocus
    self.captureEvent.set()

  def checkResult(self):
    result = CameraResult()
    if self.resultEvent.is_set():
      result = self.result
      self.result = CameraResult()
      self.resultEvent.clear()
    return result

  # Interface for inside loop to wait, capture, and set the result
  def waitToCapture(self):
    self.captureEvent.wait()
    self.captureEvent.clear()

  def setResult(self, newResult):
    self.result = newResult
    self.resultEvent.set()