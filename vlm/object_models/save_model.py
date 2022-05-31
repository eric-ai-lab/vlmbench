import os
import json
from pyrep.objects.shape import Shape
from pyrep.pyrep import PyRep

from amsolver.backend.utils import WriteCustomDataBlock, get_local_grasp_pose

class Model_Modifer(object):
    def __init__(self, all_model_dir) -> None:
        super().__init__()
        self.pr = PyRep()
        self.pr.launch('', headless=True)
        self.all_model_dir = all_model_dir

    def import_model(self, model_config):
        models = []
        class_name = model_config["class"]
        object_name = model_config["name"]
        save_path = os.path.join(self.all_model_dir, class_name, object_name)
        if not os.path.exists(save_path):
            os.makedirs(save_path)
        for i, m in enumerate(model_config["parts"]):
            part_name = m["name"]
            part = self.import_shape(m["model_path"], part_name)
            if m["graspable"]:
                WriteCustomDataBlock(part.get_handle(),"graspable","True")
            if i in model_config["manipulated_part"]:
                grasp_mesh_path = os.path.join(save_path, f"{part_name}.ply")
                # m["local_grasp_pose_path"] = grasp_mesh_path.replace('ply','pkl')
                m["local_grasp_pose_path"] = f"{part_name}.pkl"
                self.extra_grasp_poses(part, grasp_mesh_path)
            models.append(part)
        with open(os.path.join(save_path, f"{object_name}.json"), "w") as f:
            json.dump(model_config, f, indent=1)
        need_save_part = models[model_config["highest_part"]]
        need_save_part.save_model(os.path.join(save_path, f"{object_name}.ttm"))
    
    def extra_from_ttm(self, model_config, ttm_path):
        self.pr.import_model(ttm_path)
        class_name = model_config["class"]
        object_name = model_config["name"]
        save_path = os.path.join(self.all_model_dir, class_name, object_name)
        if not os.path.exists(save_path):
            os.makedirs(save_path)
        for i, m in enumerate(model_config["parts"]):
            part = Shape(m["orginal_name"])
            part_name = m["name"]
            part.set_name(part_name)
            part.compute_mass_and_inertia(1000)
            part.set_renderable(False)
            part.set_respondable(True)
            part.set_dynamic(True)
            part.set_collidable(True)
            if m["graspable"]:
                WriteCustomDataBlock(part.get_handle(),"graspable","True")
            for children in part.get_objects_in_tree(exclude_base=True, first_generation_only=True):
                if "visible" in children.get_name() or "visual" in children.get_name():
                    children.set_name(part_name+"_visual")
                    children.set_renderable(True)
            if i in model_config["manipulated_part"]:
                if "local_grasp_pose_path" in m:
                    pose_path = os.path.join(save_path, "{}.pkl".format(m["local_grasp_pose_path"]))
                    if os.path.exists(pose_path):
                        m["local_grasp_pose_path"] = "{}.pkl".format(m["local_grasp_pose_path"])
                        continue
                grasp_mesh_path = os.path.join(save_path, f"{part_name}.ply")
                m["local_grasp_pose_path"] = f"{part_name}.pkl"
                self.extra_grasp_poses(part, grasp_mesh_path)

        with open(os.path.join(save_path, f"{object_name}.json"), "w") as f:
            json.dump(model_config, f, indent=1)
        need_save_part = Shape(model_config["parts"][model_config["highest_part"]]["name"])
        # for m in need_save_part.get_objects_in_tree(exclude_base=False):
        #     if "waypoint" in m.get_name():
        #         m.remove()
        if not need_save_part.is_model():
            need_save_part.set_model(True)
        need_save_part.save_model(os.path.join(save_path, f"{object_name}.ttm"))

    @staticmethod
    def extra_grasp_poses(grasp_obj, mesh_path):
        need_rebuild= True if not os.path.exists(mesh_path) else False
        crop_box = None
        for m in grasp_obj.get_objects_in_tree(exclude_base=True, first_generation_only=True):
            if "crop" in m.get_name():
                crop_box = m
                break
        grasp_pose = get_local_grasp_pose(grasp_obj, mesh_path, grasp_pose_path=os.path.dirname(mesh_path),
                need_rebuild = need_rebuild, crop_box=crop_box, use_meshlab=True)
    
    def object_json(self):
        obj_property = {
            "graspable"
        }
        
    def import_shape(self, model_path, name, save_path=None):
        model = Shape.import_shape(model_path, reorient_bounding_box=True)
        try:
            model = self.pr.merge_objects(model.ungroup())
        except:
            pass
        model.set_name(name)
        model_visual = model.copy()
        model_visual.reorient_bounding_box()
        model_visual.set_parent(model)
        model_visual.set_name(name+'_visual')
        model_visual.set_renderable(True)
        model_visual.set_respondable(False)
        model_visual.set_dynamic(False)

        model.set_transparency(0)
        model.get_convex_decomposition(morph=True,individual_meshes=True, use_vhacd=True, vhacd_pca=False)
        model.reorient_bounding_box()
        model.compute_mass_and_inertia(1000)
        model.set_renderable(False)
        model.set_respondable(True)
        model.set_dynamic(True)
        model.set_model(True)
        if save_path is not None:
            model.save_model(os.path.join(self.all_model_dir, f"{name}.ttm"))
        return model

if __name__=="__main__":
    modifer = Model_Modifer("./vlm/object_models")
    model_config = {
        "class": "cube",
        "name": "cube_normal",
        "articulated": False,
        "constraints": None,
        "highest_part":0,
        "manipulated_part":[0],
        "parts":[
            {
                "name": "cube_normal",
                "model_path": "./vlm/object_models/cube.ply",
                "graspable": True,
                "local_grasp_pose_path":None,
                "property":{
                    "shape": "cube",
                    "size": "medium",
                    "color": None,
                    "relative_pos": None
                }
            }
        ]
    }
    model_config_large = {
        "class": "cube",
        "name": "cube_large",
        "articulated": False,
        "constraints": None,
        "highest_part":0,
        "manipulated_part":[0],
        "parts":[
            {
                "name": "cube_large",
                "model_path": "./vlm/object_models/cube_large.ply",
                "graspable": True,
                "local_grasp_pose_path":None,
                "property":{
                    "shape": "cube",
                    "size": "large",
                    "color": None,
                    "relative_pos": None
                }
            }
        ]
    }
    model_config_small = {
        "class": "cube",
        "name": "cube_small",
        "articulated": False,
        "constraints": None,
        "highest_part":0,
        "manipulated_part":[0],
        "parts":[
            {
                "name": "cube_small",
                "model_path": "./vlm/object_models/cube_small.ply",
                "graspable": True,
                "local_grasp_pose_path":None,
                "property":{
                    "shape": "cube",
                    "size": "small",
                    "color": None,
                    "relative_pos": None
                }
            }
        ]
    }
    model_config_door1 = {
        "class": "door",
        "name": "door1",
        "articulated": True,
        "constraints": {
            "door_frame_joint":[0, 1],
            "door_handle_joint":[1, 2]
        },
        "highest_part":0,
        "manipulated_part":[2],
        "parts":[
            {
                "orginal_name":"door_frame",
                "name": "door1_frame",
                "graspable": False,
                "property":{
                    "shape": "The frame of door",
                    "color": None,
                    "size": None,
                    "relative_pos": None
                }
            },
            {
                "orginal_name":"door_main",
                "name": "door1_main",
                "graspable": False,
                "property":{
                    "shape": "The door",
                    "color": None,
                    "size": None,
                    "relative_pos": None
                }
            },
            {
                "orginal_name":"open_door_handle",
                "name": "door1_handle",
                "graspable": False,
                "property":{
                    "shape": "The handle of door",
                    "color": None,
                    "size": None,
                    "relative_pos": None
                }
            }
        ]
    }
    model_config_door2 = {
        "class": "door",
        "name": "door2",
        "articulated": True,
        "constraints": {
            "Revolute_left_door_joint":[0, 1],
            "Revolute_left_handle_joint":[1, 2]
        },
        "highest_part":0,
        "manipulated_part":[2],
        "parts":[
            {
                "orginal_name":"door2_left_base",
                "name": "door2_frame",
                "graspable": False,
                "property":{
                    "shape": "The frame of door",
                    "color": None,
                    "size": None,
                    "relative_pos": None
                }
            },
            {
                "orginal_name":"door2_left_door",
                "name": "door2_main",
                "graspable": False,
                "property":{
                    "shape": "The door",
                    "color": None,
                    "size": None,
                    "relative_pos": None
                }
            },
            {
                "orginal_name":"door2_left_handler",
                "name": "door2_handle",
                "graspable": False,
                "property":{
                    "shape": "The handle of door",
                    "color": None,
                    "size": None,
                    "relative_pos": None
                }
            }
        ]
    }
    mc_drawer1 = {
        "class": "drawer",
        "name": "drawer1",
        "articulated": True,
        "constraints": {
            "drawer_joint_top":[0, 1],
            "drawer_joint_middle":[0, 2],
            "drawer_joint_bottom":[0, 3]
        },
        "highest_part":0,
        "manipulated_part":[1,2,3],
        "parts":[
            {
                "orginal_name":"drawer_frame",
                "name": "drawer1_frame",
                "graspable": False,
                "property":{
                    "shape": "the frame of drawer",
                    "color": None,
                    "size": None,
                    "relative_pos": None
                }
            },
            {
                "orginal_name":"drawer_top",
                "name": "drawer1_top",
                "graspable": False,
                "local_grasp_pose_path": "drawer1_top",
                "property":{
                    "shape": "drawer",
                    "color": None,
                    "size": None,
                    "relative_pos": None
                }
            },
            {
                "orginal_name":"drawer_middle",
                "name": "drawer1_middle",
                "graspable": False,
                "local_grasp_pose_path": "drawer1_top",
                "property":{
                    "shape": "drawer",
                    "color": None,
                    "size": None,
                    "relative_pos": None
                }
            },
            {
                "orginal_name":"drawer_bottom",
                "name": "drawer1_bottom",
                "graspable": False,
                "local_grasp_pose_path": "drawer1_top",
                "property":{
                    "shape": "drawer",
                    "color": None,
                    "size": None,
                    "relative_pos": None
                }
            }
        ]
    }
    star_config = {
        "class": "star",
        "name": "star_normal",
        "articulated": False,
        "constraints": None,
        "highest_part":0,
        "manipulated_part":[0],
        "parts":[
            {
                "orginal_name":"star",
                "name": "star_normal",
                "graspable": True,
                "property":{
                    "shape": "star",
                    "color": None,
                    "size": None,
                    "relative_pos": None
                }
            }
        ]
    }
    moon_config = {
        "class": "moon",
        "name": "moon_normal",
        "articulated": False,
        "constraints": None,
        "highest_part":0,
        "manipulated_part":[0],
        "parts":[
            {
                "orginal_name":"moon",
                "name": "moon_normal",
                "graspable": True,
                "property":{
                    "shape": "moon",
                    "color": None,
                    "size": None,
                    "relative_pos": None
                }
            }
        ]
    }
    triangular_config = {
        "class": "triangular",
        "name": "triangular_normal",
        "articulated": False,
        "constraints": None,
        "highest_part":0,
        "manipulated_part":[0],
        "parts":[
            {
                "orginal_name":"triangular_prism",
                "name": "triangular_normal",
                "graspable": True,
                "property":{
                    "shape": "triangular",
                    "color": None,
                    "size": None,
                    "relative_pos": None
                }
            }
        ]
    }
    cylinder_config = {
        "class": "cylinder",
        "name": "cylinder_normal",
        "articulated": False,
        "constraints": None,
        "highest_part":0,
        "manipulated_part":[0],
        "parts":[
            {
                "orginal_name":"cylinder",
                "name": "cylinder_normal",
                "graspable": True,
                "property":{
                    "shape": "cylinder",
                    "color": None,
                    "size": None,
                    "relative_pos": None
                }
            }
        ]
    }
    cube_basic_config = {
        "class": "cube",
        "name": "cube_basic",
        "articulated": False,
        "constraints": None,
        "highest_part":0,
        "manipulated_part":[0],
        "parts":[
            {
                "orginal_name":"cube",
                "name": "cube_basic",
                "graspable": True,
                "property":{
                    "shape": "cube",
                    "color": None,
                    "size": None,
                    "relative_pos": None
                }
            }
        ]
    }
    mug_config = {
        "class": "mug",
        "name": "mug1",
        "articulated": False,
        "constraints": None,
        "highest_part":0,
        "manipulated_part":[0],
        "parts":[
            {
                "orginal_name":"cup_target",
                "name": "mug1",
                "graspable": True,
                "property":{
                    "shape": "mug",
                    "color": None,
                    "size": None,
                    "relative_pos": None
                }
            }
        ]
    }
    mug2_config = {
        "class": "mug",
        "name": "mug2",
        "articulated": False,
        "constraints": None,
        "highest_part":0,
        "manipulated_part":[0],
        "parts":[
            {
                "orginal_name":"mug2",
                "name": "mug2",
                "graspable": True,
                "property":{
                    "shape": "mug",
                    "color": None,
                    "size": None,
                    "relative_pos": None
                }
            }
        ]
    }
    pencile1_config = {
        "class": "pencil",
        "name": "pencil1",
        "articulated": False,
        "constraints": None,
        "highest_part":0,
        "manipulated_part":[0],
        "parts":[
            {
                "orginal_name":"pencil1",
                "name": "pencil1",
                "graspable": True,
                "property":{
                    "shape": "pencil",
                    "color": None,
                    "size": None,
                    "relative_pos": None
                }
            }
        ]
    }
    wiper1_config = {
        "class": "wiper",
        "name": "sponge",
        "articulated": False,
        "constraints": None,
        "highest_part":0,
        "manipulated_part":[0],
        "parts":[
            {
                "orginal_name":"sponge",
                "name": "sponge",
                "graspable": True,
                "property":{
                    "shape": "sponge",
                    "color": None,
                    "size": None,
                    "relative_pos": None
                }
            }
        ]
    }
    modifer.extra_from_ttm(pencile1_config,"./vlm/object_models/pencil/pencil1_original.ttm")
    modifer.pr.shutdown()