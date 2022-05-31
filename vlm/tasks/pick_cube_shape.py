from typing import List
import numpy as np
from amsolver.backend.unit_tasks import VLM_Object, TargetSpace
from pyrep.objects.shape import Shape
from amsolver.const import colors
from amsolver.backend.utils import select_color
from vlm.tasks.pick_cube import PickCube

object_dict = {
            "star":{
                "path":"star/star_normal/star_normal.ttm"
            },
            "moon":{
                "path":"moon/moon_normal/moon_normal.ttm"
            },
            "triangular":{
                "path":"triangular/triangular_normal/triangular_normal.ttm"
            },
            "cylinder":{
                "path":"cylinder/cylinder_normal/cylinder_normal.ttm"
            },
            "cube":{
                "path":"cube/cube_basic/cube_basic.ttm"
            }
        }

class PickCubeShape(PickCube):

    def init_episode(self, index: int) -> List[str]:
        self.object_list = [self.shape_lib[index]]
        other_obj_index = list(range(len(self.shape_lib)))
        other_obj_index.remove(index)
        distractor_number = np.random.randint(1,len(self.shape_lib))
        distractor_index = np.random.choice(other_obj_index, distractor_number, replace=False)
        for i in distractor_index:
            self.object_list.append(self.shape_lib[i])
        color_index = np.random.choice(len(colors), len(self.object_list), replace=True)
        for i, obj in enumerate(self.object_list):
            Shape(obj.manipulated_part.visual).set_color(colors[color_index[i]][1])
            # obj.manipulated_part.descriptions = "the {} {}".format(colors[color_index[i]][0], obj.manipulated_part.property["shape"])
            obj.manipulated_part.descriptions = "the {}".format(obj.manipulated_part.property["shape"])

        target_space_colors = np.random.choice(len(colors), len(self.target_spaces), replace=False)
        for i, target_space in enumerate(self.target_spaces):
            target_space.target_space_descriptions = "the {} container".format(colors[target_space_colors[i]][0])
            Shape(target_space.focus_obj_id).set_color(colors[target_space_colors[i]][1])

        return super().init_episode(index)
    
    def variation_count(self) -> int:
        return len(object_dict)

    def import_objects(self, num):
        object_numbers = [1]*len(object_dict)
        self.shape_lib = []
        for obj, num in zip(object_dict, object_numbers):
            for i in range(num):
                model = VLM_Object(self.pyrep, self.model_dir+object_dict[obj]["path"], i)
                model.set_parent(self.taks_base)
                model.set_position([0,0,0])
                self.shape_lib.append(model)
        self.register_graspable_objects(self.shape_lib)
                