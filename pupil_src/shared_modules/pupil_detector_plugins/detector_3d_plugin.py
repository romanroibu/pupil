from pupil_detectors import PupilDetector, Detector3D
from .detector_base_plugin import PupilDetectorPlugin

from pyglui import ui
from pyglui.cygl.utils import draw_gl_texture

from gl_utils import (
    adjust_gl_view,
    clear_gl_screen,
    basic_gl_setup,
    make_coord_system_norm_based,
    make_coord_system_pixel_based,
)
from plugin import Plugin
from .visualizer_3d import Eye_Visualizer


class Detector3DPlugin(PupilDetectorPlugin):
    uniqueness = 'unique'
    icon_font = 'pupil_icons'
    icon_chr = chr(0xec19)

    def __init__(self, g_pool = None, namespaced_properties = None, detector_3d: Detector3D = None):
        super().__init__(g_pool=g_pool)
        self.detector_3d = detector_3d or Detector3D(namespaced_properties or {})
        #debug window
        self.debugVisualizer3D = Eye_Visualizer(g_pool, self.detector_3d.focal_length())

    def detect(self, frame, user_roi, visualize, pause_video = False):
        return self.detector_3d.detect(
            frame,
            user_roi,
            visualize,
            pause_video,
            is_debugging_enabled=self.is_debug_window_open
        )

    @property
    def detector_properties_2d(self) -> dict:
        return self.detector_3d.detector_properties_2d

    @property
    def detector_properties_3d(self) -> dict:
        return self.detector_3d.detector_properties_3d

    @property
    def pupil_detector(self) -> PupilDetector:
        return self.detector_3d

    ### PupilDetectorPlugin API

    @classmethod
    def parse_pretty_class_name(cls) -> str:
        return "Pupil Detector 3D"

    def init_ui(self):
        Plugin.add_menu(self)
        self.menu.label = self.pretty_class_name
        info = ui.Info_Text("Switch to the algorithm display mode to see a visualization of pupil detection parameters overlaid on the eye video. "\
                                +"Adjust the pupil intensity range so that the pupil is fully overlaid with blue. "\
                                +"Adjust the pupil min and pupil max ranges (red circles) so that the detected pupil size (green circle) is within the bounds.")
        self.menu.append(info)
        #self.menu.append(ui.Switch('coarse_detection',self.detector_properties_2d,label='Use coarse detection'))
        self.menu.append(ui.Slider('intensity_range',self.detector_properties_2d,label='Pupil intensity range',min=0,max=60,step=1))
        self.menu.append(ui.Slider('pupil_size_min',self.detector_properties_2d,label='Pupil min',min=1,max=250,step=1))
        self.menu.append(ui.Slider('pupil_size_max',self.detector_properties_2d,label='Pupil max',min=50,max=400,step=1))
        #self.menu.append(ui.Slider('ellipse_roundness_ratio',self.detector_properties_2d,min=0.01,max=1.0,step=0.01))
        #self.menu.append(ui.Slider('initial_ellipse_fit_treshhold',self.detector_properties_2d,min=0.01,max=6.0,step=0.01))
        #self.menu.append(ui.Slider('canny_treshold',self.detector_properties_2d,min=1,max=1000,step=1))
        #self.menu.append(ui.Slider('canny_ration',self.detector_properties_2d,min=1,max=4,step=1))
        info_3d = ui.Info_Text("Open the debug window to see a visualization of the 3D pupil detection." )
        self.menu.append(info_3d)
        self.menu.append(ui.Button('Reset 3D model', self.reset_model))
        self.menu.append(ui.Button('Open debug window',self.debug_window_toggle))
        model_sensitivity_slider = ui.Slider(
            'model_sensitivity',
            self.detector_properties_3d,
            label='Model sensitivity',
            min=0.990,
            max=1.0,
            step=0.0001,
        )
        model_sensitivity_slider.display_format = '%0.4f'
        self.menu.append(model_sensitivity_slider)
        self.menu.append(
            ui.Switch(
                'model_is_frozen',
                self.detector_properties_3d,
                label='Freeze model',
            )
        )
        # self.menu.append(ui.Slider('pupil_radius_min',self.detector_properties_3d,label='Pupil min radius', min=1.0,max= 8.0,step=0.1))
        # self.menu.append(ui.Slider('pupil_radius_max',self.detector_properties_3d,label='Pupil max radius', min=1.0,max=8.0,step=0.1))
        # self.menu.append(ui.Slider('max_fit_residual',self.detector_properties_3d,label='3D fit max residual', min=0.00,max=0.1,step=0.0001))
        # self.menu.append(ui.Slider('max_circle_variance',self.detector_properties_3d,label='3D fit max circle variance', min=0.01,max=2.0,step=0.001))
        # self.menu.append(ui.Slider('combine_evaluation_max',self.detector_properties_3d,label='3D fit max combinations eval', min=500,max=50000,step=5000))
        # self.menu.append(ui.Slider('combine_depth_max',self.detector_properties_3d,label='3D fit max combination depth', min=10,max=5000,step=20))
        #advanced_controls_menu = ui.Growing_Menu('Advanced Controls')
        #advanced_controls_menu.append(ui.Slider('contour_size_min',self.detector_properties_2d,label='Contour min length',min=1,max=200,step=1))
        #sidebar.append(advanced_controls_menu)

    def gl_display(self):
        self.debug_window_update()

    def deinit_ui(self):
        Plugin.remove_menu(self)

    def cleanup(self):
        self.debug_window_close() # if we change detectors, be sure debug window is also closed

    # Public

    def reset_model(self):
         self.detector_3d.reset_model()

    # Debug window management

    @property
    def is_debug_window_open(self) -> bool:
        return self.debugVisualizer3D.window is not None

    def debug_window_toggle(self):
        if not self.is_debug_window_open:
            self.debug_window_open()
        else:
            self.debug_window_close()

    def debug_window_open(self):
        if not self.is_debug_window_open:
            self.debugVisualizer3D.open_window()

    def debug_window_close(self):
        if self.is_debug_window_open:
            self.debugVisualizer3D.close_window()

    def debug_window_update(self):
        if self.is_debug_window_open:
            self.debugVisualizer3D.update_window(self.g_pool, self.detector_3d.debug_result)