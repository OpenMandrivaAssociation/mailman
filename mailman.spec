%define uid     mail
%define gid     mail
%define email_version   2.5.8

Name:       mailman
Version:    2.1.12
Release:    %mkrel 1
Summary:    The GNU Mailing List Management System
Group:      System/Servers
License:    GPL
URL:        http://www.list.org/
Source0:    http://prdownloads.sourceforge.net/mailman/%{name}-%{version}.tgz
Source1:    %{name}.init
Patch0:     %{name}-buildroot-check.patch
Patch1:     mailman-2.1.12-rename-arch.patch
Patch6:     %{name}-2.1.2-postfix-aliases.patch
Patch8:     %{name}-2.1.5-build.patch
Patch9:     %{name}-2.1.11-change-default-icons-url.patch
Requires:   mail-server
Requires:   apache
%py_requires -d
# webapp macros and scriptlets
Requires(post):     mail-server
Requires(post):     rpm-helper >= 0.18
Requires(preun):    rpm-helper
Requires(postun):   rpm-helper >= 0.16
BuildRequires:      rpm-helper >= 0.18
BuildRequires:      rpm-mandriva-setup >= 1.23
BuildRoot:          %{_tmppath}/%{name}-%{version}

%description
Mailman -- The GNU Mailing List Management System --
is a mailing list management system written mostly in
Python. Features:

  o Most standard mailing list features, including:
     moderation, mail based commands, digests, etc...
  o An extensive Web interface, customizable on a per-list basis.
  o Web based list administration interface for *all* admin-type tasks
  o Automatic Web based hypermail-style archives (using pipermail or
    other external archiver), including provisions for private archives
  o Integrated mail list to newsgroup gatewaying
  o Integrated newsgroup to mail list gatewaying (polling-based... if you
     have access to the nntp server, you should be able to easily do
     non-polling based news->mail list gatewaying; email viega@list.org,
     I'd like to help get that going and come up
     with instructions)
  o Smart bounce detection and correction
  o Integrated fast bulk mailing
  o Smart spam protection
  o Extensible logging
  o Multiple list owners and moderators are possible
  o Optional MIME-compliant digests
  o Nice about which machine you subscribed from if you're from the
        right domain

Conditional build options:
    mailman uid --with uid %{uid}
    mailman gid --with gid %{gid}

%prep
%setup -q
%patch0 -p1 -b .buildroot
%patch1 -p1 -b .rename-arch
%patch6 -p1 -b .chmod
%patch8
%patch9 -p1 -b .default
#%patch10 -p0 -b .deprecation
#%patch11 -p0 -b .email
#%patch12 -p0 -b .exceptions

%build
%serverbuild
# As a normal user, we don't have permissions to do this.  %patch0 changes
#   configure so that the directory check will never fail.
autoreconf
./configure \
    --prefix=%{_libdir}/%{name} \
    --with-var-prefix=%{_var}/lib/%{name} \
    --with-mail-gid=%{gid} \
    --with-cgi-gid=apache \
    --with-username=%{uid} \
    --with-groupname=%{gid} \
    --without-permcheck \
    --libdir=%{_libdir}

make
# fix encoding typo
perl -pi -e 's/gb2132/gb2312/' misc/email-2.5.6/email/Charset.py

%install
rm -rf %{buildroot}
%makeinstall_std

# mv web content
install -d -m 755 %{buildroot}%{_var}/www
mv %{buildroot}%{_libdir}/%{name}/cgi-bin %{buildroot}%{_var}/www/%{name}
mv %{buildroot}%{_libdir}/%{name}/icons %{buildroot}%{_var}/www/%{name}

# apache conf
install -d -m 755 %{buildroot}%{_webappconfdir}
cat > %{buildroot}%{_webappconfdir}/%{name}.conf <<EOF
# Mailman Apache configuration file
Alias /%{name}   %{_var}/www/%{name}
Alias /pipermail %{_var}/lib/%{name}/archives/public

<Directory %{_var}/www/%{name}>
    Options ExecCgi
    <Files ~ "^(listinfo|admin|admindb|confirm|create|edithtml|options|private|rmlist|roster|subscribe)$">
        SetHandler cgi-script
    </Files>
    DirectoryIndex listinfo
    Allow from all
</Directory>

<Directory %{_var}/lib/mailman/archives/public>
    Options FollowSymlinks
    Allow from all
</Directory>
EOF

# init script
install -d -m 755 %{buildroot}%{_initrddir}
install -m 755 misc/mailman %{buildroot}%{_initrddir}

# (sb) sendmail 
install -d -m 755 %{buildroot}%{_sysconfdir}/smrsh
(cd %{buildroot}%{_sysconfdir}/smrsh && ln -s ../..%{_libdir}/%{name}/mail/%{name} .)

# move logs directory into /var/log
install -d -m 755 %{buildroot}%{_var}/log
mv %{buildroot}%{_var}/lib/%{name}/logs %{buildroot}%{_var}/log/%{name}
(cd %{buildroot}%{_var}/lib/%{name} && ln -s ../../log/%{name} logs)

# move config file into /etc
install -d -m 755 %{buildroot}%{_sysconfdir}
mv %{buildroot}%{_libdir}/%{name}/Mailman/mm_cfg.py %{buildroot}%{_sysconfdir}/%{name}
(cd %{buildroot}%{_libdir}/%{name}/Mailman && ln -s ../../../..%{_sysconfdir}/%{name} mm_cfg.py)
rm -f %{buildroot}%{_libdir}/%{name}/Mailman/mm_cfg.py.dist

# fix permissions mess
chmod -R go=u-ws %{buildroot}%{_libdir}/%{name}
chmod -R go=u-ws %{buildroot}%{_var}/lib/%{name}
chmod 750 %{buildroot}%{_var}/lib/%{name}/archives/private

# logrotate
install -d m 755 %{buildroot}%{_sysconfdir}/logrotate.d
cat > %{buildroot}%{_sysconfdir}/logrotate.d/%{name} <<EOF
%{_var}/log/mailman/smtp-failure {
    daily
    missingok
    rotate 7
}

%{_var}/log/mailman/smtp {
    daily
    missingok
    rotate 7
}

%{_var}/log/mailman/locks {
    daily
    missingok
    rotate 7
}

%{_var}/log/mailman/fromusenet {
    daily
    missingok
    rotate 7
}

%{_var}/log/mailman/qrunner {
    daily
    missingok
    rotate 7
}
%{_var}/log/mailman/bounce {
    weekly
    missingok
    rotate 4
}

%{_var}/log/mailman/digest {
    monthly
    missingok
    rotate 4
}

%{_var}/log/mailman/error {
    weekly
    missingok
    rotate 4
}

%{_var}/log/mailman/vette {
    weekly
    missingok
    rotate 4
}

%{_var}/log/mailman/mischief {
    weekly
    missingok
    rotate 4
}

%{_var}/log/mailman/subscribe {
    monthly
    missingok
    rotate 12
}

%{_var}/log/mailman/post {
    monthly
    missingok
    rotate 12
}
EOF

# install init script
install -m 755 %{SOURCE1} %{buildroot}%{_initrddir}/%{name}

# binaries symlinks from /usr/sbin
install -d -m 755 %{buildroot}%{_sbindir}
pushd %{buildroot}%{_sbindir}
for bin in ../..%{_libdir}/%{name}/bin/*; do
    ln -s $bin .
done
popd

cat > README.mdv <<EOF
Mandriva RPM specific notes

setup
-----
The setup used here differs from default one, to achieve better FHS compliance.
- the configuration file is /etc/mailman
- the log files are in /var/log/mailman
- the constant files are in /usr/lib/mailman
- the variable files are in /var/lib/mailman
Moreover, the perms used are most standard and secures. check_perms will
scream, but mailman runs fine.

post-installation
-----------------
Post-installation script attempts first to integrate mailman aliases file with
existing mail aliases. Then the server-wide 'mailman' list is automatically
created, with root@hostname as admin, and a randomly generated password. This
list is configured with generic default values, but its configuration should be
reviewed before usage.
The password is available in the notification message sent by mailman upon list
creation, and is also used as the site password. The mailman service has to be
started, and the SMTP server has to be running for the message to be correctly
delivered.

upgrade
-------
The alias db (/var/lib/mailman/data/aliases.db) should be owned by the same uid
and gid as the one used by mailman, mail.mail here. You may experience toubles
when upgrading from old releases of the packages.
EOF

# for some unknow reason, those files are sometime missing
[ -d %{buildroot}%{_libdir}/%{name}/pythonlib/korean ] || exit

%pre
if [ $1 = "2" ]; then
  if [ ! -L %{_libdir}/%{name}/Mailman/mm_cfg.py ]; then
    mv %{_libdir}/%{name}/Mailman/mm_cfg.py %{_sysconfdir}/%{name}.tmp
  fi
  if [ ! -L %{_var}/lib/%{name}/logs ]; then
    mv %{_var}/lib/%{name}/logs %{_var}/log/%{name}
  fi
fi

%post
%_post_service %{name}
%_post_webapp

cd %{_libdir}/%{name}

if [ $1 = 1 ]; then
    # installation

    # generic tasks
    hostname=`hostname`
    domainname=`dnsdomainname`

    # mailman basic configuration
    cat >>Mailman/mm_cfg.py <<EOF
DEFAULT_EMAIL_HOST = '$domainname'
DEFAULT_URL_HOST = '$hostname'
add_virtualhost(DEFAULT_URL_HOST, DEFAULT_EMAIL_HOST)
EOF

    # make sure mail user is allowed to use cron
    if [ -f %{_sysconfdir}/cron.allow ]; then
        if ! grep -q %{uid} %{_sysconfdir}/cron.allow; then
            echo "%{uid}" >> %{_sysconfdir}/cron.allow
        fi
    fi

    # add cron task
    crontab -u %{uid} %{_libdir}/%{name}/cron/crontab.in

    # add aliases
    %create_ghostfile %{_var}/lib/%{name}/data/aliases %{uid} %{gid} 660
    mta="`readlink /etc/alternatives/sendmail-command 2>/dev/null | cut -d . -f 2`"
    if [ "$mta" == "postfix" ]; then
        cat >>Mailman/mm_cfg.py <<EOF
MTA = 'Postfix'
EOF
        maps=`/usr/sbin/postconf -h alias_maps`
        postconf -e \
            "recipient_delimiter = +" \
            "unknown_local_recipient_reject_code = 550" \
            "alias_maps = $maps, hash:%{_var}/lib/%{name}/data/aliases"
        /usr/sbin/postalias %{_var}/lib/%{name}/data/aliases
    else
        cat >> %{_sysconfdir}/aliases <<EOF
:include:   %{_var}/lib/%{name}/data/aliases
EOF
        /usr/bin/newaliases
    fi

    # generate random password
    passwd=%_get_password 8

    # site password
    %{_sbindir}/mmsitepass $passwd > /dev/null

    if [ ! -f /var/lib/mailman/lists/mailman/config.pck ]; then
        # initial list creation and configuration
        su %{uid} -c "%{_sbindir}/newlist mailman root@$hostname $passwd" > /dev/null
        %{_sbindir}/config_list -i /var/lib/mailman/data/sitelist.cfg mailman
    fi

else
    # upgrade
    if [ -f %{_sysconfdir}/%{name}.tmp ]; then
        mv -f %{_sysconfdir}/%{name}.tmp %{_sysconfdir}/%{name}
    fi
fi

%preun
%_preun_service %{name}

%postun
%_postun_webapp
if [ $1 = 0 ]; then
    # generic tasks

    # remove cron task
    crontab -u %{uid} -r

    # remove aliases
    mta="`readlink /etc/alternatives/sendmail-command 2>/dev/null | cut -d . -f 2`"
    if [ "$mta" == "postfix" ]; then
        database=`/usr/sbin/postconf -h alias_database | \
            sed -e 's|, hash:%{_var}/lib/%{name}/data/aliases||'`
        maps=`/usr/sbin/postconf -h alias_maps | \
            sed -e 's|, hash:%{_var}/lib/%{name}/data/aliases||'`
        postconf -e \
            "alias_database = $database" \
            "alias_maps = $maps"
    else
        sed -i -e '/:include:   %{_var}/lib/%{name}/data/aliases/d' \
            %{_sysconfdir}/aliases
    fi
    /usr/bin/newaliases
fi

%clean
rm -rf %{buildroot}

%files
%defattr(-,root,root)
%doc ACKNOWLEDGMENTS BUGS FAQ INSTALL NEWS README* TODO UPGRADING
%doc gnu-COPYING-GPL contrib/README.check_perms_grsecurity
# constant files
%dir %{_libdir}/%{name}
%{_libdir}/%{name}/cron
%{_libdir}/%{name}/pythonlib
%{_libdir}/%{name}/scripts
%{_libdir}/%{name}/tests
%{_libdir}/%{name}/messages
%{_libdir}/%{name}/templates
%{_libdir}/%{name}/bin
%{_libdir}/%{name}/Mailman
%dir %{_libdir}/%{name}/mail
%attr(02755,root,%{gid}) %{_libdir}/%{name}/mail/*
# variable files
%attr(-,%{uid},%{gid}) %{_var}/lib/%{name}
%attr(-,%{uid},apache) %{_var}/lib/%{name}/archives/private
%attr(-,%{uid},%{gid}) %{_var}/log/%{name}
# configuration files
%{_initrddir}/%{name}
%config(noreplace) %{_webappconfdir}/%{name}.conf
%config(noreplace) %{_sysconfdir}/logrotate.d/%{name}
%config(noreplace) %{_sysconfdir}/%{name}
%{_sysconfdir}/smrsh/%{name}
%{_sbindir}/*
%dir %{_var}/www/%{name}
%attr(-,root,%{gid}) %{_var}/www/%{name}/admin
%attr(-,root,%{gid}) %{_var}/www/%{name}/admindb
%attr(-,root,%{gid}) %{_var}/www/%{name}/confirm
%attr(-,root,%{gid}) %{_var}/www/%{name}/create
%attr(-,root,%{gid}) %{_var}/www/%{name}/edithtml
%attr(-,root,%{gid}) %{_var}/www/%{name}/listinfo
%attr(-,root,%{gid}) %{_var}/www/%{name}/options
%attr(-,root,%{gid}) %{_var}/www/%{name}/private
%attr(-,root,%{gid}) %{_var}/www/%{name}/rmlist
%attr(-,root,%{gid}) %{_var}/www/%{name}/roster
%attr(-,root,%{gid}) %{_var}/www/%{name}/subscribe
%{_var}/www/%{name}/icons
