def update_series():
    from get_settings import get_sonarr_settings
    url_sonarr = get_sonarr_settings()[6]
    apikey_sonarr = get_sonarr_settings()[4]
    serie_default_enabled = get_general_settings()[15]
    serie_default_language = get_general_settings()[16]
    serie_default_hi = get_general_settings()[17]

    if apikey_sonarr == None:
        pass
    else:
        get_profile_list()
    
        # Get shows data from Sonarr
        url_sonarr_api_series = url_sonarr + "/api/series?apikey=" + apikey_sonarr
        try:
            r = requests.get(url_sonarr_api_series, timeout=15, verify=False)
            r.raise_for_status()
        except requests.exceptions.HTTPError as errh:
            logging.exception("Error trying to get series from Sonarr. Http error.")
        except requests.exceptions.ConnectionError as errc:
            logging.exception("Error trying to get series from Sonarr. Connection Error.")
        except requests.exceptions.Timeout as errt:
            logging.exception("Error trying to get series from Sonarr. Timeout Error.")
        except requests.exceptions.RequestException as err:
            logging.exception("Error trying to get series from Sonarr.")
        else:
            # Open database connection
            db = sqlite3.connect(os.path.join(config_dir, 'db/bazarr.db'), timeout=30)
            c = db.cursor()

            # Get current shows in DB
            current_shows_db = c.execute('SELECT tvdbId FROM table_shows').fetchall()

            # Close database connection
            db.close()

            current_shows_db_list = [x[0] for x in current_shows_db]
            current_shows_sonarr = []
            series_to_update = []
            series_to_add = []

            for show in r.json():
                try:
                    overview = unicode(show['overview'])
                except:
                    overview = ""
                try:
                    poster_big = show['images'][2]['url'].split('?')[0]
                    poster = os.path.splitext(poster_big)[0] + '-250' + os.path.splitext(poster_big)[1]
                except:
                    poster = ""
                try:
                    fanart = show['images'][0]['url'].split('?')[0]
                except:
                    fanart = ""

                # Add shows in Sonarr to current shows list
                current_shows_sonarr.append(show['tvdbId'])

                if show['tvdbId'] in current_shows_db_list:
                    series_to_update.append((show["title"],show["path"],show["tvdbId"],show["id"],overview,poster,fanart,profile_id_to_language((show['qualityProfileId'] if sonarr_version == 2 else show['languageProfileId'])),show['sortTitle'],show["tvdbId"]))
                else:
                    if serie_default_enabled is True:
                        series_to_add.append((show["title"], show["path"], show["tvdbId"], serie_default_language, serie_default_hi, show["id"], overview, poster, fanart, profile_id_to_language(show['qualityProfileId']), show['sortTitle']))
                    else:
                        series_to_add.append((show["title"], show["path"], show["tvdbId"], show["tvdbId"], show["tvdbId"], show["id"], overview, poster, fanart, profile_id_to_language(show['qualityProfileId']), show['sortTitle']))

            # Update or insert series in DB
            db = sqlite3.connect(os.path.join(config_dir, 'db/bazarr.db'), timeout=30)
            c = db.cursor()

            updated_result = c.executemany('''UPDATE table_shows SET title = ?, path = ?, tvdbId = ?, sonarrSeriesId = ?, overview = ?, poster = ?, fanart = ?, `audio_language` = ? , sortTitle = ? WHERE tvdbid = ?''', series_to_update)
            db.commit()

            if serie_default_enabled is True:
                added_result = c.executemany('''INSERT INTO table_shows(title, path, tvdbId, languages,`hearing_impaired`, sonarrSeriesId, overview, poster, fanart, `audio_language`, sortTitle) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', series_to_add)
                db.commit()
            else:
                added_result = c.executemany('''INSERT INTO table_shows(title, path, tvdbId, languages,`hearing_impaired`, sonarrSeriesId, overview, poster, fanart, `audio_language`, sortTitle) VALUES (?,?,?,(SELECT languages FROM table_shows WHERE tvdbId = ?),(SELECT `hearing_impaired` FROM table_shows WHERE tvdbId = ?), ?, ?, ?, ?, ?, ?)''', series_to_add)
                db.commit()
            db.close()

            for show in series_to_add:
                list_missing_subtitles(show[5])

            # Delete shows not in Sonarr anymore
            deleted_items = []
            for item in current_shows_db_list:
                if item not in current_shows_sonarr:
                    deleted_items.append(tuple([item]))
            db = sqlite3.connect(os.path.join(config_dir, 'db/bazarr.db'), timeout=30)
            c = db.cursor()
            c.executemany('DELETE FROM table_shows WHERE tvdbId = ?',deleted_items)
            db.commit()
            db.close()