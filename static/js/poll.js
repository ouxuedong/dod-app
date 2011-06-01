
function make_li(message) {
    li_html = '<li class="message"><div>' + message.content + '</div>' +
    '<div><form action="' + $SCRIPT_ROOT + 'create_topic" method="post">' + message.email + ' | ' + message.created_at +
    '<input type="hidden" name="title" value="On - "' + message.content + '"/>' +
    '<input type="hidden" name="parent_topic_key" value="' + message.topic_key + '" />' +
    '<input type="submit" value="Branch" /></form></li>';
    return $(li_html);
}

function go() {
    setInterval(function() {
        console.log('polling...')
        $.getJSON($SCRIPT_ROOT + 'poll', {
            topic_key: $('#topic_key').val(),
            offset: $('.message').size()
        }, function(data) {
            $.each(data.messages, function(index, message) {
                console.log(message)
                $('#message_list').prepend(make_li(message))
            })
        });
    }, 3000);
}


$(document).ready(go);
