/**
 * cjblog :: main.js
 *
 * Provides (hopefully) reliable client-side responsive scaling.
 *
 * Author: Christopher Rink (chrisrink10 at gmail dot com)
 */
$(document).ready(function() {
    var sidebar = $(".sidebar"),
        body = $(".main_body"),
        subtitle = $(".subtitle"),
        sep = $(".sep");

    // Define resizeFunc as a closure so we can cache common selectors
    var resizeFunc = function() {
        var width = $(window).width();

        // Scale the sidebar and body content appropriately
        if (width >= 1300) {
            sidebar.css("width", "24%");
            body.css("width", "73%");
            sep.hide();
        } else if (width > 975 && width < 1300) {
            sidebar.css("width", "23%");
            body.css("width", "73%");
            sep.hide();
        } else if (width > 800 && width <= 975) {
            sidebar.css("width", "22%");
            body.css("width", "73%");
            sep.hide();
        } else {
            sidebar.css("width", "95%");
            body.css("width", "95%");
            sep.show();
        }

        if (width < 550) {
            subtitle.hide();
        } else {
            subtitle.show();
        }
    }

    // Attach the resize function to the resize event
    $(window).on("resize", resizeFunc);

    // And run it once the page has loaded
    resizeFunc();
});