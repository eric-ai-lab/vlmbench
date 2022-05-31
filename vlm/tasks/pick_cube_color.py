from typing import List
import numpy as np
from amsolver.backend.unit_tasks import VLM_Object, TargetSpace
from pyrep.objects.shape import Shape
from amsolver.const import colors
from amsolver.backend.utils import scale_object, select_color
from vlm.tasks.pick_cube import PickCube

class PickCubeColor(PickCube):
    def init_task(self) -> None:
        self.model_num = 2
        return super().init_task()
        
    def init_episode(self, index: int) -> List[str]:
        for obj in self.object_list:
            scale_factor = np.random.uniform(0.8, 1.2)
            relative_factor = scale_object(obj, scale_factor)
            if abs(relative_factor-1)>1e-2:
                local_grasp_pose = obj.manipulated_part.local_grasp
                local_grasp_pose[:, :3, 3] *= relative_factor
                obj.manipulated_part.local_grasp = local_grasp_pose
                
        color_names, rgbs = select_color(index, len(self.object_list)-1)
        for i, obj in enumerate(self.object_list):
            Shape(obj.manipulated_part.visual).set_color(rgbs[i])
            obj.manipulated_part.property["color"] = color_names[i]
            obj.manipulated_part.descriptions = "the {} {}".format(color_names[i], obj.manipulated_part.property["shape"])

        target_space_colors = np.random.choice(len(colors), len(self.target_spaces), replace=False)
        for i, target_space in enumerate(self.target_spaces):
            target_space.target_space_descriptions = "the {} container".format(colors[target_space_colors[i]][0])
            Shape(target_space.focus_obj_id).set_color(colors[target_space_colors[i]][1])

        return super().init_episode(index)
    
    def variation_count(self) -> int:
        return len(colors)
    
    # def import_objects(self, num=3):
    #     if not hasattr(self, "model_path"):
    #         model_path = self.model_dir+"cube/cube_normal/cube_normal.ttm"
    #     else:
    #         model_path = self.model_dir+self.model_path
    #     self.shape_lib = []
    #     for i in range(num):
    #         cube = VLM_Object(self.pyrep, model_path, i)
    #         cube.set_parent(self.taks_base)
    #         self.shape_lib.append(cube)
    #     self.register_graspable_objects(self.object_list)