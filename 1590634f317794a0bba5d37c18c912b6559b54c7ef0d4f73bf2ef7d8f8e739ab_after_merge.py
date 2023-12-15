    async def on_PUT(self, request, user_id):
        requester = await self.auth.get_user_by_req(request)
        await assert_user_is_admin(self.auth, requester.user)

        target_user = UserID.from_string(user_id)
        body = parse_json_object_from_request(request)

        if not self.hs.is_mine(target_user):
            raise SynapseError(400, "This endpoint can only be used with local users")

        user = await self.admin_handler.get_user(target_user)
        user_id = target_user.to_string()

        if user:  # modify user
            if "displayname" in body:
                await self.profile_handler.set_displayname(
                    target_user, requester, body["displayname"], True
                )

            if "threepids" in body:
                # check for required parameters for each threepid
                for threepid in body["threepids"]:
                    assert_params_in_dict(threepid, ["medium", "address"])

                # remove old threepids from user
                threepids = await self.store.user_get_threepids(user_id)
                for threepid in threepids:
                    try:
                        await self.auth_handler.delete_threepid(
                            user_id, threepid["medium"], threepid["address"], None
                        )
                    except Exception:
                        logger.exception("Failed to remove threepids")
                        raise SynapseError(500, "Failed to remove threepids")

                # add new threepids to user
                current_time = self.hs.get_clock().time_msec()
                for threepid in body["threepids"]:
                    await self.auth_handler.add_threepid(
                        user_id, threepid["medium"], threepid["address"], current_time
                    )

            if "avatar_url" in body and type(body["avatar_url"]) == str:
                await self.profile_handler.set_avatar_url(
                    target_user, requester, body["avatar_url"], True
                )

            if "admin" in body:
                set_admin_to = bool(body["admin"])
                if set_admin_to != user["admin"]:
                    auth_user = requester.user
                    if target_user == auth_user and not set_admin_to:
                        raise SynapseError(400, "You may not demote yourself.")

                    await self.store.set_server_admin(target_user, set_admin_to)

            if "password" in body:
                if not isinstance(body["password"], str) or len(body["password"]) > 512:
                    raise SynapseError(400, "Invalid password")
                else:
                    new_password = body["password"]
                    logout_devices = True

                    new_password_hash = await self.auth_handler.hash(new_password)

                    await self.set_password_handler.set_password(
                        target_user.to_string(),
                        new_password_hash,
                        logout_devices,
                        requester,
                    )

            if "deactivated" in body:
                deactivate = body["deactivated"]
                if not isinstance(deactivate, bool):
                    raise SynapseError(
                        400, "'deactivated' parameter is not of type boolean"
                    )

                if deactivate and not user["deactivated"]:
                    await self.deactivate_account_handler.deactivate_account(
                        target_user.to_string(), False
                    )
                elif not deactivate and user["deactivated"]:
                    if "password" not in body:
                        raise SynapseError(
                            400, "Must provide a password to re-activate an account."
                        )

                    await self.deactivate_account_handler.activate_account(
                        target_user.to_string()
                    )

            user = await self.admin_handler.get_user(target_user)
            return 200, user

        else:  # create user
            password = body.get("password")
            password_hash = None
            if password is not None:
                if not isinstance(password, str) or len(password) > 512:
                    raise SynapseError(400, "Invalid password")
                password_hash = await self.auth_handler.hash(password)

            admin = body.get("admin", None)
            user_type = body.get("user_type", None)
            displayname = body.get("displayname", None)

            if user_type is not None and user_type not in UserTypes.ALL_USER_TYPES:
                raise SynapseError(400, "Invalid user type")

            user_id = await self.registration_handler.register_user(
                localpart=target_user.localpart,
                password_hash=password_hash,
                admin=bool(admin),
                default_display_name=displayname,
                user_type=user_type,
                by_admin=True,
            )

            if "threepids" in body:
                # check for required parameters for each threepid
                for threepid in body["threepids"]:
                    assert_params_in_dict(threepid, ["medium", "address"])

                current_time = self.hs.get_clock().time_msec()
                for threepid in body["threepids"]:
                    await self.auth_handler.add_threepid(
                        user_id, threepid["medium"], threepid["address"], current_time
                    )
                    if (
                        self.hs.config.email_enable_notifs
                        and self.hs.config.email_notif_for_new_users
                    ):
                        await self.pusher_pool.add_pusher(
                            user_id=user_id,
                            access_token=None,
                            kind="email",
                            app_id="m.email",
                            app_display_name="Email Notifications",
                            device_display_name=threepid["address"],
                            pushkey=threepid["address"],
                            lang=None,  # We don't know a user's language here
                            data={},
                        )

            if "avatar_url" in body and isinstance(body["avatar_url"], str):
                await self.profile_handler.set_avatar_url(
                    target_user, requester, body["avatar_url"], True
                )

            ret = await self.admin_handler.get_user(target_user)

            return 201, ret