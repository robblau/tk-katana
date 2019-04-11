import os

from Katana import FarmAPI

import sgtk

HookBaseClass = sgtk.get_hook_baseclass()


class ScanSceneHook(HookBaseClass):
    """
    Hook to scan scene for items to publish
    """

    def execute(self, **kwargs):
        """
        Main hook entry point
        :returns:       A list of any items that were found to be published.
                        Each item in the list should be a dictionary containing
                        the following keys:
                        {
                            type:   String
                                    This should match a scene_item_type defined in
                                    one of the outputs in the configuration and is
                                    used to determine the outputs that should be
                                    published for the item

                            name:   String
                                    Name to use for the item in the UI

                            description:    String
                                            Description of the item to use in the UI

                            selected:       Bool
                                            Initial selected state of item in the UI.
                                            Items are selected by default.

                            required:       Bool
                                            Required state of item in the UI.  If True then
                                            item will not be deselectable.  Items are not
                                            required by default.

                            other_params:   Dictionary
                                            Optional dictionary that will be passed to the
                                            pre-publish and publish hooks
                        }
        """
        items = []

        # get the main scene:
        scene_name = FarmAPI.GetKatanaFileName()
        if not scene_name:
            raise sgtk.TankError("Please Save your file before Publishing")

        scene_path = os.path.abspath(scene_name)
        name = os.path.basename(scene_path)

        # create the primary item - this will match the primary output 'scene_item_type':
        items.append({"type": "work_file", "name": name})

#        # if there is any geometry in the scene (poly meshes or nurbs patches), then
#        # add a geometry item to the list:
#        if cmds.ls(geometry=True, noIntermediate=True):
#            items.append({"type":"geometry", "name":"All Scene Geometry"})

        return items
