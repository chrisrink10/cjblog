/**
 * cjblog :: edit.js
 *
 * Provides a few small client-side dynamic functions for the edit form.
 *
 * Author: Christopher Rink (chrisrink10 at gmail dot com)
 */
$(document).ready(function() {
    $(".delete_link").on("click", function() {
        var delSpan = $(this).parent().parent();

        // Hide the initial delete question
        delSpan.find(".delete_question").hide();
        delSpan.find(".delete_confirmation").show();
    });

    $(".delete_no").on("click", function() {
        var delSpan = $(this).parent().parent();

        // Hide the initial delete question
        delSpan.find(".delete_question").show();
        delSpan.find(".delete_confirmation").hide();
    });
});