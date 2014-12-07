/**
 * cjblog :: edit.js
 *
 * Provides a few small client-side dynamic functions for the edit form.
 *
 * Author: Christopher Rink (chrisrink10 at gmail dot com)
 */
$(document).ready(function(){
    // Enable the Preview and Hide Preview buttons
    $("input[name='preview']").on("click", function() {
        var target = $("input[name='title_link']").val(),
            title = $("input[name='title']").val(),
            date = $("input[name='date']").val(),
            body = $("textarea[name='body']").val();

        // If a link is specified create that element
        if (target != "") {
            var link = $("#preview_link").clone(true, true);
            link.attr("href", target);
            link.html(title);
            link.show();
            $("#preview_title").empty().append(link);
        } else {
            $("#preview_title").html(title);
        }

        // Create valid HTML from the Markdown body
        $.ajax({
            'type': 'POST',
            'url': '/admin/tomarkdown',
            'data': body,
            'dataType': 'html',
            'contentType': 'text/plain'
        }).done(function(data) {
             $("#preview_body").html(data);
        });


        // Update the body and date too
        $("#preview_date").html(date);

        // Hide the form and show the preview
        $("#edit_article_form").hide();
        $("#edit_article_preview").show();
    });
    $("input[name='hide_preview']").on("click", function() {
        // Show the form and hide the preview
        $("#edit_article_form").show();
        $("#edit_article_preview").hide();
    });

    // Insert Today's date
    $("input[name='today']").on("click", function() {
        var now = "";
        // It is so much more work getting a correctly formatted date
        // string in JavaScript that AJAX up to the server is worth the trip
        $.get('/admin/now').done(function(data) {
            $("input[name='date']").val(data);
        });
    });

    // Allow canceling to return home
    $("input[name='cancel']").on("click", function() {
        var leave = window.confirm("Do you really want to leave this page?");
        if (leave) {
            window.location.href = '/admin';
        }
    });
});