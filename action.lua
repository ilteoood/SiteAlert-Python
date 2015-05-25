function on_msg_receive (msg)
	msg.text = string.lower(msg.text)
  if msg.out then
    return
  end
  if (msg.text=='ping') then
    send_msg (msg.from.print_name, 'pong', ok_cb, false)
	elseif (msg.text=='sitealert mostra') then
		cmd = 'python3 /home/pi/SiteAlert-python/SiteAlert.py -se', temp
		send_msg(msg.from.print_name, os.capture(cmd), ok_cb, false)
	elseif (string.match(msg.text,'sitealert controlla')) then
		param = explode(msg.text)
		cmd = 'python3 /home/pi/SiteAlert-python/SiteAlert.py -ae '.. param[4] .. ' ' .. param[2].. ' ' .. param[6] .. ' ' .. msg.from.print_name
		send_msg(msg.from.print_name, os.capture(cmd), ok_cb, false)
	elseif (string.match(msg.text,'sitealert aggiungimi'))then
		param = explode(msg.text)
		cmd = 'python3 /home/pi/SiteAlert-python/SiteAlert.py -ame ' .. param[2] .. ' ' .. param[4] .. ' ' .. msg.from.print_name
		send_msg(msg.from.print_name, os.capture(cmd), ok_cb, false)
	elseif (string.match(msg.text,'sitealert rimuovimi'))then
		param = explode(msg.text)
		cmd = 'python3 /home/pi/SiteAlert-python/SiteAlert.py -re '.. param[2] .. ' ' .. param[3] .. ' ' .. msg.from.print_name
		send_msg(msg.from.print_name, os.capture(cmd), ok_cb, false)
	else
		cmd = 'Ciao '.. msg.from.print_name .. '!\nBenvenuto nel bot di @SiteAlert.\nComandi disponibili:\nsitealert controlla _link_ chiamandolo _nome_ avvisandomi _mail_\nsitealert aggiungimi _nome_ avvisandomi _mail_\nsitealert mostra\nsitealert rimuovimi _nome_ _mail_\nTest: ping'
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