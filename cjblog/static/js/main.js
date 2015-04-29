/**
 * cjblog :: main.js
 *
 * Author: Christopher Rink (chrisrink10 at gmail dot com)
 */
$(document).ready(function() {
    $(".article_date a").on("mouseover", function() {
        $(".article_permalink", this).show();
    }).on("mouseout", function() {
        $(".article_permalink", this).hide();
    });
});