import os
import time

from piui import PiUi

current_dir = os.path.dirname(os.path.abspath(__file__))


class TimelapsePiUi(object):

  def __init__(self, camera, idy, convert):
    self._ui = PiUi(img_dir=os.path.join(current_dir))
    self._camera = camera
    self._idy = idy
    self._convert = convert

  def thumbname(self, filename):
    return filename[:filename.rfind('.')] + "_thumb" + filename[filename.rfind('.'):]

  def show_config(self, configs, current):
    config = self._configs[self._current_config]
    self.exp.set_text("T: %s ISO: %d" % (config[0], config[1]))

  def show_status(self, shot, configs, current):
    config = self._configs[self._current_config]
    self.title.set_text("Shot %d" % shot)
    self.exp.set_text("T: %s ISO: %d" % (config[0], config[1]))

  def should_stop(self):
    return self._stop

  def show_error(self, err):
    self.title.set_text(err)

  def ondownclick(self):
    self._current_config -= 1
    if self._current_config < 0:
      self._current_config = 0
    self.show_config(self._configs, self._current_config)

  def onupclick(self):
    self._current_config += 1
    if self._current_config > len(self._configs):
      self._current_config = len(self._configs) - 1
    self.show_config(self._configs, self._current_config)

  def onstartclick(self):
    self._done = True

  def onstopclick(self):
    self.title.set_text("Stopping...")
    self._stop = True

  def onpreviewclick(self):
    self.title.set_text("Capturing Preview...")
    config = self._configs[self._current_config]
    try:
      self._camera.set_shutter_speed(secs=config[0])
      self._camera.set_iso(iso=str(config[1]))
    except Exception, e:
      self.title.set_text(str(e))
    filename = None
    brightness = 0.0
    try:
      filename = self._camera.capture_image_and_download()
    except Exception, e:
      self.title.set_text(str(e))
    if filename:
      brightness = float(self._idy.mean_brightness(filename))
    self._convert.thumbnail(filename, self.thumbname(filename))
    filename = self.thumbname(filename)
    self.img.set_src(filename[filename.rfind('/')+1:])
    self.title.set_text("Preview: %f [25k tgt]" % brightness)
    
  def new_frame(self, filename, brightness):
    self._convert.thumbnail(filename, self.thumbname(filename))
    filename = self.thumbname(filename)
    self.img.set_src(filename[filename.rfind('/')+1:])
    self.bright.set_text("br: %f" % brightness)


  def main(self, configs, current_config, network_status):
    self._configs = configs
    self._current_config = current_config
    self.page = self._ui.new_ui_page(title="Timelapse")
    self.title = self.page.add_textbox("Initial Exposure", "h3")
    self.exp = self.page.add_textbox("", "h2")
    plus = self.page.add_button("--&uarr;--", self.onupclick)
    minus = self.page.add_button("--&darr;--", self.ondownclick)
    preview = self.page.add_button("Preview", self.onpreviewclick)
    start = self.page.add_button("Start", self.onstartclick)
    self.page.add_element('br')
    self.img = self.page.add_image("")
    self._done = False
    self.show_config(self._configs, self._current_config)
    # The app sits in this wait loop until we're ready to move into
    # shooting mode.  Note that the onstartclick (etc) methods will
    # be called on other thread(s)
    while not self._done:
        time.sleep(0.1)

    self.page = self._ui.new_ui_page(title="Shooting")
    self.title = self.page.add_textbox("", "h2")
    self.exp = self.page.add_textbox("", "h3")
    stop = self.page.add_button("Stop", self.onstopclick)
    self.page.add_element('br')
    self.img = self.page.add_image("")
    self.page.add_element("br")
    self.bright = self.page.add_textbox("", "p")
    self._stop = False
    return self._current_config

