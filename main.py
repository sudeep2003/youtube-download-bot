from pytube import YouTube


def download_audio(url):
    if url != "" and "youtube" in url:
        yt = YouTube(url)
    else:
        print("You should enter a valid link")
        return
    print("Wait a moment...")
    # Get the list of available audio streams
    audio_streams = yt.streams.filter(only_audio=True)
    if not audio_streams:
        print("No audio streams available")
        return
    # Print the available audio streams
    print("Available audio streams:")
    for i, stream in enumerate(audio_streams):
        print(f"{i + 1}. {stream.abr} kbps - {stream.default_filename}")
    # Get the user's selection
    try:
        selection = int(input("Enter the number of the audio stream you want to download: "))
        if selection < 1 or selection > len(audio_streams):
            raise IndexError
        selected_stream = audio_streams[selection - 1]
    except (ValueError, IndexError):
        print("Invalid selection")
        return
    try:
        print("File founded wait a little bit...")
        selected_stream.download()
        print("Download is completed successfully")
    except Exception as e:
        print(f"An error has occurred: {e}")


link = input("Enter the YouTube video URL: ")
download_audio(link)
