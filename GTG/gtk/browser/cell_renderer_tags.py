# -----------------------------------------------------------------------------
# Getting Things GNOME! - a personal organizer for the GNOME desktop
# Copyright (c) 2008-2013 - Lionel Dricot & Bertrand Rousseau
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program.  If not, see <http://www.gnu.org/licenses/>.
# -----------------------------------------------------------------------------

from gi.repository import GObject, GLib, Gtk, Gdk
from gi.repository import Pango
import gi
import cairo
gi.require_version('PangoCairo', '1.0')
# XXX: disable PEP8 checking on this line to prevent an E402 error due to
#      require_version needing to be called before the PangoCairo import
from gi.repository import PangoCairo  # noqa


class CellRendererTags(Gtk.CellRenderer):

    SYMBOLIC_ICONS = (
        'emblem-documents-symbolic',
        'task-past-due-symbolic',
        'system-search-symbolic',
    )

    __gproperties__ = {
        'tag_list': (GObject.TYPE_PYOBJECT,
                     "Tag list", "A list of tags", GObject.ParamFlags.READWRITE),
        'tag': (GObject.TYPE_PYOBJECT, "Tag",
                "Tag", GObject.ParamFlags.READWRITE),
    }

    # Private methods
    def __roundedrec(self, context, x, y, w, h, r=10):
        "Draw a rounded rectangle"
        #   A  *  BQ
        #  H       C
        #  *       *
        #  G       D
        #   F  *  E

        context.move_to(x + r, y)          # Move to A
        context.line_to(x + w - r, y)      # Line to B

        context.curve_to(
            x + w, y,
            x + w, y,
            x + w, y + r
        )  # Curve to C
        context.line_to(x + w, y + h - r)  # Line to D

        context.curve_to(
            x + w, y + h,
            x + w, y + h,
            x + w - r, y + h
        )  # Curve to E
        context.line_to(x + r, y + h)      # Line to F

        context.curve_to(
            x, y + h,
            x, y + h,
            x, y + h - r
        )  # Curve to G
        context.line_to(x, y + r)          # Line to H

        context.curve_to(
            x, y,
            x, y,
            x + r, y
        )  # Curve to A
        return

    def __count_viewable_tags(self):

        count = 0
        if self.tag_list is not None:
            for my_tag in self.tag_list:
                my_tag_color = my_tag.get_attribute("color")
                my_tag_icon = my_tag.get_attribute("icon")
                if my_tag_color or my_tag_icon:
                    count = count + 1
        elif self.tag is not None:
            count = 1
        else:
            count = 0

        return count

    # Class methods
    def __init__(self, config):
        super().__init__()
        self.tag_list = None
        self.tag = None
        self.xpad = 1
        self.ypad = 1
        self.PADDING = 1
        self.config = config
        self._ignore_icon_error_for = set()

    def do_set_property(self, pspec, value):
        if pspec.name == "tag-list":
            self.tag_list = value
        else:
            setattr(self, pspec.name, value)

    def do_get_property(self, pspec):
        if pspec.name == "tag-list":
            return self.tag_list
        else:
            return getattr(self, pspec.name)

    def do_render(self, cr, widget, background_area, cell_area, flags):

        vw_tags = self.__count_viewable_tags()
        count = 0

        # Select source
        if self.tag_list is not None:
            tags = self.tag_list
        elif self.tag is not None:
            tags = [self.tag]
        else:
            return

        if self.config.get('dark_mode'):
            symbolic_color = Gdk.RGBA(0.9, 0.9, 0.9, 1)
        else:
            symbolic_color = Gdk.RGBA(0, 0, 0, 1)

        # Drawing context
        gdkcontext = cr

        # Coordinates of the origin point
        x_align = self.get_property("xalign")
        y_align = self.get_property("yalign")
        padding = self.PADDING
        orig_x = cell_area.x + int(
            (cell_area.width - 16 * vw_tags - padding * 2 * (vw_tags - 1)) * x_align)
        orig_y = cell_area.y + int(
            (cell_area.height - 16) * y_align)

        # We draw the icons & squares
        for my_tag in tags:

            my_tag_icon = my_tag.get_attribute("icon")
            my_tag_color = my_tag.get_attribute("color")

            rect_x = orig_x + self.PADDING * 2 * count + 16 * count
            rect_y = orig_y

            if my_tag_icon:
                if my_tag_icon in self.SYMBOLIC_ICONS:
                    icon_theme = Gtk.IconTheme.get_default()
                    scale_factor = widget.get_scale_factor()
                    info = icon_theme.lookup_icon_for_scale(my_tag_icon, 16,
                                                            scale_factor, 0)
                    pixbuf, was_symbolic = info.load_symbolic(symbolic_color)

                    surface = Gdk.cairo_surface_create_from_pixbuf(
                        pixbuf, scale_factor, widget.get_window())
                    Gtk.render_icon_surface(
                        widget.get_style_context(), gdkcontext, surface,
                        rect_x, rect_y)

                    count += 1

                else:
                    layout = PangoCairo.create_layout(cr)
                    layout.set_markup(my_tag_icon, -1)
                    cr.move_to(rect_x - 2, rect_y - 1)
                    PangoCairo.show_layout(cr, layout)
                    count += 1

            elif my_tag_color:

                # Draw rounded rectangle
                my_color = Gdk.RGBA()
                my_color.parse(my_tag_color)
                Gdk.cairo_set_source_rgba(gdkcontext, my_color)

                self.__roundedrec(gdkcontext, rect_x, rect_y, 16, 16, 8)
                gdkcontext.fill()
                count += 1

                # Outer line
                Gdk.cairo_set_source_rgba(gdkcontext, Gdk.RGBA(0, 0, 0, 0.20))
                gdkcontext.set_line_width(1.0)
                self.__roundedrec(gdkcontext, rect_x, rect_y, 16, 16, 8)
                gdkcontext.stroke()

        if self.tag and my_tag:

            my_tag_icon = my_tag.get_attribute("icon")
            my_tag_color = my_tag.get_attribute("color")

            if not my_tag_icon and not my_tag_color:
                # Draw rounded rectangle
                Gdk.cairo_set_source_rgba(gdkcontext,
                                          Gdk.RGBA(0.95, 0.95, 0.95, 1))
                self.__roundedrec(gdkcontext, rect_x, rect_y, 16, 16, 8)
                gdkcontext.fill()

                # Outer line
                Gdk.cairo_set_source_rgba(gdkcontext, Gdk.RGBA(0, 0, 0, 0.20))
                gdkcontext.set_line_width(1.0)
                self.__roundedrec(gdkcontext, rect_x, rect_y, 16, 16, 8)
                gdkcontext.stroke()

    def do_get_size(self, widget, cell_area=None):
        count = self.__count_viewable_tags()

        if count != 0:
            return (self.xpad, self.ypad,
                    self.xpad * 2 + 16 * count + 2 * count * self.PADDING,
                    16 + 2 * self.ypad)
        else:
            return (self.xpad, self.ypad, self.xpad * 2, self.ypad * 2)


GObject.type_register(CellRendererTags)
