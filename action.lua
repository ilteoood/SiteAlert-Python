function on_msg_receive (msg)
	msg.text = msg.text:gsub("^%l", string.lower)
  if msg.out then
    return
  end
  if (msg.text=='ping') then
    send_msg (msg.from.print_name, 'pong', ok_cb, false)
	elseif (msg.text=='mostra') then
		cmd = 'python3 /home/pi/SiteAlert-python/SiteAlert.py -se', temp
		send_msg(msg.from.print_name, os.capture(cmd), ok_cb, false)
	elseif (string.match(msg.text,'controlla')) then
		param = explode(msg.text)
		cmd = 'python3 /home/pi/SiteAlert-python/SiteAlert.py -ae '.. param[3] .. ' ' .. param[1].. ' ' .. param[5] .. ' ' .. msg.from.print_name
		send_msg(msg.from.print_name, os.capture(cmd), ok_cb, false)
	elseif (string.match(msg.text,'aggiungimi'))then
		param = explode(msg.text)
		cmd = 'python3 /home/pi/SiteAlert-python/SiteAlert.py -ame ' .. param[1] .. ' ' .. param[3] .. ' ' .. msg.from.print_name
		send_msg(msg.from.print_name, os.capture(cmd), ok_cb, false)
	elseif (string.match(msg.text,'rimuovimi'))then
		param = explode(msg.text)
		cmd = 'python3 /home/pi/SiteAlert-python/SiteAlert.py -re '.. param[1] .. ' ' .. param[2] .. ' ' .. msg.from.print_name
		send_msg(msg.from.print_name, os.capture(cmd), ok_cb, false)
	else
		cmd = 'Ciao '.. msg.from.print_name .. '!\nBenvenuto nel bot di @SiteAlert.\nComandi disponibili:\ncontrolla _link_ chiamandolo _nome_ avvisandomi _mail_\naggiungimi _nome_ avvisandomi _mail_\nmostra\nrimuovimi _nome_ _mail_\nTest: ping'
		send_msg(msg.from.print_name, cmd, ok_cb, false)
  end
end

function on_our_id (id)
end

function on_secret_chat_created (peer)
end

function on_user_update (user)
end

function on_chat_update (user)
end

function on_get_difference_end ()
end

function on_binlog_replay_end ()
end

function os.capture(cmd)
    local handle = assert(io.popen(cmd, 'r'))
    local output = assert(handle:read('*a'))
    
    handle:close()
   
    --[[output = string.gsub(
        string.gsub(
            string.gsub(output, '^%s+', ''), 
            '%s+$', 
            ''
        ), 
        '[\n\r]+',
        ' '
    )]]--
   
   return string.sub(output, 7)
end

function explode(str)
	local k = 0
	array = {}
	for i in string.gmatch(str, "%S+") do
		array[k] = i
		k = k+1
	end
	return array
end