# Copyright (c) 2017 Shotgun Software Inc.
#
# CONFIDENTIAL AND PROPRIETARY
#
# This work is provided "AS IS" and subject to the Shotgun Pipeline Toolkit
# Source Code License included in this distribution package. See LICENSE.
# By accessing, using, copying or modifying this work you indicate your
# agreement to the Shotgun Pipeline Toolkit Source Code License. All rights
# not expressly granted therein are reserved by Shotgun Software Inc.

import errno
import os
import textwrap

import sgtk
from sgtk.platform.qt import QtGui

from Katana import NodegraphAPI

HookBaseClass = sgtk.get_hook_baseclass()


class LookFilePublishWidgetItem(QtGui.QWidget):
    """
    A Widget to list all the versions of Look Files generated by a node.
    """
    def __init__(self, name, data, parent=None):
        """
        Initialize the class.

        :param name: The node name.
        :type name: str
        :param data: The data used to populate this node.
        :type data: dict
        :type parent: QtGui.QWidget
        """
        super(LookFilePublishWidgetItem, self).__init__(parent=None)
        self.__name = name
        layout = QtGui.QHBoxLayout()
        self.setLayout(layout)
        label = QtGui.QLabel(self.__name, parent=self)
        layout.addWidget(label)
        self._combo = QtGui.QComboBox(parent=self)
        layout.addWidget(self._combo)
        self._populate(self._combo, data)

    @staticmethod
    def _populate(combo, data):
        """
        Populate a combo box with the data provided.

        :param combo:
        :type combo: QtGui.QComboBox
        :param data: The data to set on the combo box.
        :type data: dict
        """
        work_paths = data.get("work_paths", [])
        for index, path in enumerate(work_paths):
            base_name = os.path.basename(path)
            combo.addItem(base_name, userData=path)
        index = combo.findText(os.path.basename(data.get("to_publish", "")))
        if index:
            combo.setCurrentIndex(index)

    def getData(self):
        """
        Get the data from this widget.

        :rtype: dict
        """
        work_paths = []
        current_index = self._combo.currentIndex()
        to_publish = self._combo.itemData(current_index)
        for index in range(self._combo.count()):
            path = self._combo.itemData(index)
            work_paths.append(path)
        return {
            self.__name: {
                "work_paths": work_paths,
                "to_publish": to_publish
            }
        }


class LookFilePublishWidget(QtGui.QWidget):
    """
    Widget that contains all the :class:`LookFilePublishWidgetItem` generated by the 
    current publisher selection.
    """
    def __init__(self, parent=None, description_widget=None):
        """
        Initialize the widget.

        :param parent: The parent widget
        :type: QtGio                                                                                            
        """
        super(LookFilePublishWidget, self).__init__(parent=parent)
        self.__contents = {}
        self.__displayed = []
        layout = QtGui.QVBoxLayout()
        self.setLayout(layout)
        if description_widget:
            layout.addWidget(description_widget)
        row = QtGui.QHBoxLayout()
        row.addWidget(QtGui.QLabel("<b>Node Name</b>"))
        row.addWidget(QtGui.QLabel("<b>Version</b>"))
        layout.addLayout(row)

    def clear(self):
        """
        Clear the current itmtmSui
        """
        for widget in self.__displayed:
            self.layout().removeWidget(widget)
            widget.setVisible(False)
        self.__displayed = []

    def addItem(self, name, data):
        """
        Add an item to this widget
        """
        if name in self.__contents:
            widget = self.__contents[name]
        else:
            widget = LookFilePublishWidgetItem(name, data, parent=self)
            self.__contents[name] = widget
        self.layout().addWidget(widget)
        self.__displayed.append(widget)
        widget.setVisible(True)

    def getData(self):
        """
        Get the data for the selected nodes
        """
        data = {}
        for widget in self.__displayed:
            data.update(widget.getData())
        return {"node_settings": data}


class KatanaLookFilePublishPlugin(HookBaseClass):
    """
    Plugin for publishing an open katana session.

    This hook relies on functionality found in the base file publisher hook in
    the publish2 app and should inherit from it in the configuration. The hook
    setting for this plugin should look something like this::

        hook: "{self}/publish_file.py:{engine}/tk-multi-publish2/basic/publish_session.py"

    """
    @property
    def name(self):
        """The general name for this plugin (:class:`str`)."""
        return "KatanaLookFilePublish"

    @property
    def icon(self):
        """
        The path to an icon on disk that is representative of this plugin
        (:class:`str`).
        """
        return os.path.join(self.disk_location, "icons", "look_file.png")

    @property
    def description(self):
        """
        Verbose, multi-line description of what the plugin does. This can
        contain simple html for formatting.
        """

        return textwrap.dedent("""
        Publish the Look File by picking the unpublished version
        from the drop-down.

        If you can't see the version you are expecting make sure it 
        hasn't already been published, or if it has been written out.
        """)

    @property
    def settings(self):
        """
        Dictionary defining the settings that this plugin expects to receive
        through the settings parameter in the accept, validate, publish and
        finalize methods.

        A dictionary on the following form::

            {
                "Settings Name": {
                    "type": "settings_type",
                    "default": "default_value",
                    "description": "One line description of the setting"
            }

        The type string should be one of the data types that toolkit accepts as
        part of its environment configuration.
        """
        return {
            "node_settings": {
                "type": "dict",
                "default": {},
                "description": ""
            },
            "node": {
                "type": "str",
                "default": "",
                "description": ""
            },
        }

    @property
    def item_filters(self):
        """
        List of item types that this plugin is interested in.

        Only items matching entries in this list will be presented to the
        accept() method. Strings can contain glob patters such as *, for example
        ["katana.*", "file.katana"]
        """
        return ["katana.session.lookfile"]

    @staticmethod
    def _get_item_settings(settings):
        """
        Get the settings relating to the node given in the settings.

        :param settings: Settings object

        :rtype: dict
        """
        node = settings["node"].value
        all_settings = settings["node_settings"].value
        node_settings = all_settings.get(node, {})
        return node_settings

    @staticmethod
    def _set_item_settings(node_settings, settings):
        """
        Update the settings with the given dictionary.

        :param node_settings: The settings to apply.
        :param settings: The settings object to apply to.
        """
        node = settings["node"].value
        all_settings = settings["node_settings"].value
        all_settings[node] = node_settings

    def accept(self, settings, item):
        """
        Method called by the publisher to determine if an item is of any
        interest to this plugin. Only items matching the filters defined via the
        item_filters property will be presented to this method.

        A publish task will be generated for each item accepted here. Returns a
        dictionary with the following booleans:

            - accepted: Indicates if the plugin is interested in this value at
                all. Required.
            - enabled: If True, the plugin will be enabled in the UI, otherwise
                it will be disabled. Optional, True by default.
            - visible: If True, the plugin will be visible in the UI, otherwise
                it will be hidden. Optional, True by default.
            - checked: If True, the plugin will be checked in the UI, otherwise
                it will be unchecked. Optional, True by default.

        :param settings: Dictionary of Settings. The keys are strings, matching
            the keys returned in the settings property. The values are `Setting`
            instances.
        :param item: Item to process

        :returns: dictionary with boolean keys accepted, required and enabled
        """
        settings["node"].value = item.name
        node = NodegraphAPI.GetNode(item.name)
        path_param = node.getParameter("sg_saveTo")
        path = path_param.getValue(0)
        item.properties["path"] = path
        work_param = node.getParameter("sg_work_template")
        work_template_name = work_param.getValue(0)
        work_template = self._get_template(work_template_name)
        item.properties["work_template"] = work_template

        fields = work_template.validate_and_get_fields(path)
        if not fields:
            self.logger.debug(
                "'{}': '{}', is not a valid path".format(item.name, path)
            )
            return {"accepted": False, "visible": False, "enabled": False, "checked": False}
        del fields["version"]

        work_paths = self.sgtk.abstract_paths_from_template(work_template, fields)
        if not work_paths:
            self.logger.debug(
                "'{}': No generated work files".format(item.name)
            )
            return {"accepted": False, "visible": True, "enabled": True, "checked": False}

        publish_param = node.getParameter("sg_publish_template")
        publish_template_name = publish_param.getValue(0)
        publish_template = self._get_template(publish_template_name)
        item.properties["publish_template"] = publish_template
        publish_paths = self.sgtk.abstract_paths_from_template(publish_template, fields)

        work_paths_to_publish = sorted(work_paths, reverse=True)
        publish_fields = {}
        for work_path in work_paths:
            work_fields = work_template.get_fields(work_path)
            self.logger.debug("Checking '{}'".format(work_path))
            for publish_path in publish_paths:
                # cache result as this might be slow
                if publish_path not in publish_fields:
                    publish_fields[publish_path] = publish_template.get_fields(publish_path)
                publish_fields = publish_fields[publish_path]
                if os.path.exists(publish_path) and publish_fields["version"] == work_fields["version"]:
                    self.logger.debug("'{}' already published".format(work_path))
                    # publish version exists
                    work_paths_to_publish.remove(work_path)
                    break

        if not work_paths_to_publish:
            self.logger.debug(
                "'{}': All versions published".format(item.name)
            )
            return {"accepted": False, "visible": True, "enabled": True, "checked": False}

        settings_dict = {
            "work_paths": work_paths_to_publish,
            "to_publish": work_paths_to_publish[0],
        }
        self._set_item_settings(settings_dict, settings)

        return {
            "accepted": True,
            "checked": True
        }
    
    @staticmethod
    def _get_template(template_name):
        """
        Get the template object from the given name.

        :param template_name: The name of the template to retrieve.
        :returns: The template object.
        """
        engine = sgtk.platform.current_engine()
        return engine.get_template_by_name(template_name)

    def validate(self, settings, item):
        """
        Validates the given item to check that it is ok to publish. Returns a
        boolean to indicate validity.

        :param settings: Dictionary of Settings. The keys are strings, matching
            the keys returned in the settings property. The values are `Setting`
            instances.
        :param item: Item to process
        :returns: True if item is valid, False otherwise.
        """
        item_settings = self._get_item_settings(settings)
        # Check the templates exist
        work_template = item.properties["work_template"]
        if not work_template:
            raise sgtk.TankError("'{}': Work template '{}' doesn't exist".format(item.name, work_template.name))
        publish_template = item.properties["publish_template"]
        if not publish_template:
            raise sgtk.TankError("'{}': Publish template '{}' doesn't exist".format(item.name, publish_template.name))
        # Check the file exists still. It might have been removed from the filesystem after collection
        path = item_settings["to_publish"]
        if not os.path.exists(path):
            raise sgtk.TankError("The file '{}' no longer exists on disk. Has it been deleted/published?".format(path))
        # Check the filepath is valid
        if not work_template.validate(path):
            raise sgtk.TankError("The filepath '{}' does not match the template '{}'".format(path, work_template.name))
        # Check if file has already been copied to the publish location
        fields = work_template.validate_and_get_fields(path)
        publish_path = publish_template.apply_fields(fields)
        item.properties["publish_path"] = publish_path
        item.properties["path"] = path
        if os.path.exists(publish_path):
            raise IOError(errno.EEXIST, "The file '{}' has already been copied to the publish location.".format(path))

        return True

    def publish(self, settings, item):
        """
        Executes the publish logic for the given item and settings.

        :param settings: Dictionary of Settings. The keys are strings, matching
            the keys returned in the settings property. The values are `Setting`
            instances.
        :param item: Item to process
        """
        publish_path = item.properties["publish_path"]
        publish_dir = os.path.dirname(publish_path)

        self.logger.debug("Making directory: '{}'".format(publish_dir))
        engine = sgtk.platform.current_engine()
        engine.ensure_folder_exists(publish_dir)

        item.properties["publish_type"] = "Katana Look File"

        super(KatanaLookFilePublishPlugin, self).publish(settings, item)

    def create_settings_widget(self, parent):
        """
        Creates a Qt widget, for the supplied parent widget (a container widget
        on the right side of the publish UI).

        :param parent: The parent to use for the widget being created
        :return: A QtGui.QWidget or subclass that displays information about
            the plugin and/or editable widgets for modifying the plugin's
            settings.
        """
        description_widget = super(KatanaLookFilePublishPlugin, self).create_settings_widget(None)
        return LookFilePublishWidget(parent=parent, description_widget=description_widget) 

    def get_ui_settings(self, widget):
        """
        Invoked by the Publisher when the selection changes. This method gathers the settings
        on the previously selected task, so that they can be later used to repopulate the
        custom UI if the task gets selected again. They will also be passed to the accept, validate,
        publish and finalize methods, so that the settings can be used to drive the publish process.

        The widget argument is the widget that was previously created by
        `create_settings_widget`.

        The method returns a dictionary, where the key is the name of a
        setting that should be updated and the value is the new value of that
        setting. Note that it is up to you how you want to store the UI's state as
        settings and you don't have to necessarily to return all the values from
        the UI. This is to allow the publisher to update a subset of settings
        when multiple tasks have been selected.

        Example::

            {
                 "setting_a": "/path/to/a/file"
            }

        :param widget: The widget that was created by `create_settings_widget`
        """
        return widget.getData()

    def set_ui_settings(self, widget, settings):
        """
        Allows the custom UI to populate its fields with the settings from the
        currently selected tasks.

        The widget is the widget created and returned by
        `create_settings_widget`.

        A list of settings dictionaries are supplied representing the current
        values of the settings for selected tasks. The settings dictionaries
        correspond to the dictionaries returned by the settings property of the
        hook.

        Example::

            settings = [
            {
                 "seeting_a": "/path/to/a/file"
                 "setting_b": False
            },
            {
                 "setting_a": "/path/to/a/file"
                 "setting_b": False
            }]

        The default values for the settings will be the ones specified in the
        environment file. Each task has its own copy of the settings.

        When invoked with multiple settings dictionaries, it is the
        responsibility of the custom UI to decide how to display the
        information. If you do not wish to implement the editing of multiple
        tasks at the same time, you can raise a ``NotImplementedError`` when
        there is more than one item in the list and the publisher will inform
        the user than only one task of that type can be edited at a time.

        :param widget: The widget that was created by `create_settings_widget`
        :param settings: a list of dictionaries of settings for each selected
            task.
        """
        widget.clear()
        for setting in settings:
            node_name = setting["node"]
            node_settings = setting.get("node_settings", {})
            data = node_settings.get(node_name, {})
            widget.addItem(node_name, data)
