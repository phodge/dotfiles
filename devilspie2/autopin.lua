local window_class = get_window_class()
local app_name = get_application_name()
if (window_class == "Mattermost"
    or window_class == "Spotify"
    or app_name == "Spotify"
    or app_name == 'Rhythmbox'
) then
    print(string.format("Pinning %s/%s", window_class, app_name))
    pin_window()
end
