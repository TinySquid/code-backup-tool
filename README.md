# What

This is a tool I wrote in Python meant to backup source code / docs from one directory to another, while applying exclusion filters.

# Why

Because of this deficiency with Google Drive:

    It is not possible to exclude subfolders from a folder tree that you have told the Backup & Sync app to monitor.

I wanted to sync my dev folder but exclude certain files and folders (node_modules... pycache, etc) so that my Drive could then sync the rest to the cloud.

Here is the initial doc I created to identify and solve this problem [Goals](Goals.md)

I also wanted to code something useful for myself instead of cheesy toy apps, while still getting practice in.

### Why not just use a repository for your code?

1. Some of my code and resources I don't want to put up into a repo..
2. Not all of it is code either so it feels messy to have that in a repo.
3. If I make changes somewhere and don't commit them.. They won't be updated obviously.
4. Too lazy to git pull all the time if I did use a repo
5. I don't even think you can have repos inside repos...

# Future plans

1. Convert into a service so it runs on startup and watches the filesystem for changes to backup.
2. Find ways to optimize - One issue being that currently it creates a duplicate list from the source paths and only changes the parent dir to the backup-dest dir... Literally doubling the memory usage. I can remove that and just have it convert on the fly instead.
3. Clean up the code.
4. Allow for full commandline only operation as a second option (instead of loading from a config file)
