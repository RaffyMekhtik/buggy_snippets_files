    def create_settings(self):
        self.image_name = cps.ImageNameSubscriber(
                "Select the input image", cps.NONE, doc="""\
Choose the image to be cropped.""")

        self.cropped_image_name = cps.CroppingNameProvider(
                "Name the output image", "CropBlue", doc="""\
Enter the name to be given to cropped image.""")

        self.shape = cps.Choice(
                "Select the cropping shape",
                [SH_RECTANGLE, SH_ELLIPSE, SH_IMAGE,
                 SH_OBJECTS, SH_CROPPING],
                SH_RECTANGLE, doc="""\
Select the shape into which you would like to crop:

-  *%(SH_RECTANGLE)s:* Self-explanatory.
-  *%(SH_ELLIPSE)s:* Self-explanatory.
-  *%(SH_IMAGE)s:* Cropping will occur based on a binary image you
   specify. A choice box with available images will appear from which
   you can select an image. To crop into an arbitrary shape that you
   define, choose *%(SH_IMAGE)s* and use the **LoadSingleImage** module
   to load a black and white image that you have already prepared from a
   file. If you have created this image in a program such as Photoshop,
   this binary image should contain only the values 0 and 255, with
   zeros (black) for the parts you want to remove and 255 (white) for
   the parts you want to retain. Alternately, you may have previously
   generated a binary image using this module (e.g., using the
   *%(SH_ELLIPSE)s* option) and saved it using the **SaveImages**
   module.
   In any case, the image must be exactly the same starting size as your
   image and should contain a contiguous block of white pixels, because
   the cropping module may remove rows and columns that are completely
   blank.
-  *%(SH_OBJECTS)s:* Crop based on labeled objects identified by a
   previous **Identify** module.
-  *%(SH_CROPPING)s:* The cropping generated by a previous cropping
   module. You will be able to select images that were generated by
   previous **Crop** modules. This **Crop** module will use the same
   cropping that was used to generate whichever image you choose.
""" % globals())

        self.crop_method = cps.Choice(
                "Select the cropping method",
                [CM_COORDINATES, CM_MOUSE], CM_COORDINATES, doc="""\
Choose whether you would like to crop by typing in pixel coordinates or
clicking with the mouse.

-  *%(CM_COORDINATES)s:* For *%(SH_ELLIPSE)s*, you will be asked to
   enter the geometric parameters of the ellipse. For
   *%(SH_RECTANGLE)s*, you will be asked to specify the coordinates of
   the corners.
-  *%(CM_MOUSE)s:* For *%(SH_ELLIPSE)s*, you will be asked to click
   five or more points to define an ellipse around the part of the image
   you want to analyze. Keep in mind that the more points you click, the
   longer it will take to calculate the ellipse shape. For
   *%(SH_RECTANGLE)s*, you can click as many points as you like that
   are in the interior of the region you wish to retain.
""" % globals())

        self.individual_or_once = cps.Choice(
                "Apply which cycle's cropping pattern?",
                [IO_INDIVIDUALLY, IO_FIRST], IO_INDIVIDUALLY, doc="""\
Specify how a given cropping pattern should be applied to other image cycles:

-  *%(IO_FIRST)s:* The cropping pattern from the first image cycle is
   applied to all subsequent cyles. This is useful if the first image is
   intended to function as a template in some fashion.
-  *%(IO_INDIVIDUALLY)s:* Every image cycle is cropped individually.
""" % globals())

        self.horizontal_limits = cps.IntegerOrUnboundedRange(
                "Left and right rectangle positions",
                minval=0, doc="""\
*(Used only if "%(SH_RECTANGLE)s" selected as cropping shape, or if using Plate Fix)*

Specify the left and right positions for the bounding rectangle by selecting one of the following:

-  *%(ABSOLUTE)s:* Specify these values as absolute pixel coordinates in
   the original image. For instance, you might enter “25”, “225”, and
   “Absolute” to create a 200×200 pixel image that is 25 pixels from the
   top-left corner.
-  *%(FROM_EDGE)s:* Specify the position relative to the image edge.
   For instance, you might enter “25”, “25”, and “Edge” to crop 25
   pixels from both the left and right edges of the image, irrespective
   of the image’s original size.
""" % globals())

        self.vertical_limits = cps.IntegerOrUnboundedRange(
                "Top and bottom rectangle positions",
                minval=0, doc="""\
*(Used only if "%(SH_RECTANGLE)s" selected as cropping shape, or if using Plate Fix)*

Specify the top and bottom positions for the bounding rectangle by selecting one of the following:

-  *%(ABSOLUTE)s:* Specify these values as absolute pixel coordinates.
   For instance, you might enter “25”, “225”, and “Absolute” to create a
   200×200 pixel image that’s 25 pixels from the top-left corner.
-  *%(FROM_EDGE)s:* Specify position relative to the image edge. For
   instance, you might enter “25”, “25”, and “Edge” to crop 25 pixels
   from the edges of your images irrespective of their size.
""" % globals())

        self.ellipse_center = cps.Coordinates(
                "Coordinates of ellipse center",
                (500, 500), doc="""\
*(Used only if "%(SH_ELLIPSE)s" selected as cropping shape)*

Specify the center pixel position of the ellipse.""" % globals())

        self.ellipse_x_radius = cps.Integer(
                "Ellipse radius, X direction", 400, doc="""\
*(Used only if "%(SH_ELLIPSE)s" selected as cropping shape)*

Specify the radius of the ellipse in the X direction.""" % globals())

        self.ellipse_y_radius = cps.Integer(
                "Ellipse radius, Y direction", 200, doc="""\
*(Used only if "%(SH_ELLIPSE)s" selected as cropping shape)*

Specify the radius of the ellipse in the Y direction.""" % globals())

        self.image_mask_source = cps.ImageNameSubscriber(
                "Select the masking image", cps.NONE, doc="""\
*(Used only if "%(SH_IMAGE)s" selected as cropping shape)*

Select the image to be use as a cropping mask.""" % globals())

        self.cropping_mask_source = cps.CroppingNameSubscriber(
                "Select the image with a cropping mask", cps.NONE, doc="""\
*(Used only if "%(SH_CROPPING)s" selected as cropping shape)*

Select the image associated with the cropping mask that you want to use.""" % globals())

        self.objects_source = cps.ObjectNameSubscriber(
                "Select the objects", cps.NONE, doc="""\
*(Used only if "%(SH_OBJECTS)s" selected as cropping shape)*

Select the objects that are to be used as a cropping mask.""" % globals())

        self.remove_rows_and_columns = cps.Choice(
                "Remove empty rows and columns?",
                [RM_NO, RM_EDGES, RM_ALL],
                RM_ALL, doc="""\
Use this option to choose whether to remove rows and columns that lack
objects:

-  *%(RM_NO)s:* Leave the image the same size. The cropped areas will
   be set to zeroes, and will appear as black.
-  *%(RM_EDGES)s:* Crop the image so that its top, bottom, left and
   right are at the first non-blank pixel for that edge.
-  *%(RM_ALL)s:* Remove any row or column of all-blank pixels, even
   from the internal portion of the image.""" % globals())