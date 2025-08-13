import os
import watchdog
import logging
from .logIt import logIt, printIt, lable

class piDirWatcher:
  def __init__(self):
    self.dataframes = dict()

  def add_file(self, src_path):
    printIt(f'file_added: {src_path}',lable.INFO)

  def remove_file(self, src_path):
    printIt(f'file_removed: {src_path}',lable.INFO)

  def update_file(self, src_path):
    printIt(f'file_update: {src_path}',lable.INFO)

  def update_dir(self, src_path):
    printIt(f'dir_updated: {src_path}',lable.INFO)


class fsEventHander(watchdog.events.FileSystemEventHandler):

  def __init__(self):
    super().__init__()
    fsEventHander.state_watcher = piDirWatcher()

  def dispatch(self, event):
    if (event.is_directory): # or (not (event.src_path.endswith('.csv'))):
        # becuse dir events fire as updates when file events fire
        fsEventHander.state_watcher.update_dir(event.src_path)
        return
    super().dispatch(event)

  def on_created(self, event):
    fsEventHander.state_watcher.add_file(event.src_path)
  def on_deleted(self, event):
    fsEventHander.state_watcher.remove_file(event.src_path)
  def on_modified(self, event):
    fsEventHander.state_watcher.update_file(event.src_path)
  def on_moved(self, event):
    fsEventHander.state_watcher.add_file(event.dest_path)
    fsEventHander.state_watcher.remove_file(event.src_path)

