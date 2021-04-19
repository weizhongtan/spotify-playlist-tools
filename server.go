package main

import (
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"regexp"

	"github.com/gin-gonic/gin"
	"github.com/zmb3/spotify"

	"github.com/gin-contrib/sessions"
	"github.com/gin-contrib/sessions/cookie"
	"github.com/joho/godotenv"
	"golang.org/x/oauth2"
)

const redirectURL = "http://localhost:8080/callback/"
const state = "foobar"

func main() {
	err := godotenv.Load()
	if err != nil {
		log.Fatal("Error loading .env file")
	}

	r := gin.Default()

	store := cookie.NewStore([]byte("secret"))
	r.Use(sessions.Sessions("mysession", store))

	clientID := os.Getenv("CLIENT_ID")
	secretKey := os.Getenv("CLIENT_SECRET")

	auth := spotify.NewAuthenticator(redirectURL, spotify.ScopeUserReadPrivate, spotify.ScopePlaylistReadPrivate)

	auth.SetAuthInfo(clientID, secretKey)

	url := auth.AuthURL(state)

	r.GET("/auth", func(c *gin.Context) {
		c.Redirect(http.StatusFound, url)
	})

	r.GET("/callback", func(c *gin.Context) {
		session := sessions.Default(c)

		token, err := auth.Token(state, c.Request)
		if err != nil {
			c.String(http.StatusNotFound, "Couldn't get token")
			return
		}

		jsonToken, err := json.Marshal(token)
		if err != nil {
			fmt.Println(err)
			c.JSON(http.StatusInternalServerError, gin.H{
				"message": "failed",
			})
			return
		}
		session.Set("token", jsonToken)
		session.Save()
		c.Redirect(http.StatusFound, "/")
	})

	r.GET("/search", func(c *gin.Context) {
		trackNameQuery := c.Query("track_name")

		session := sessions.Default(c)

		tok, ok := session.Get("token").([]byte)
		if !ok {
			c.String(http.StatusInternalServerError, "you need to authenticate")
			return
		}

		token := &oauth2.Token{}
		json.Unmarshal(tok, token)

		client := auth.NewClient(token)

		user, err := client.CurrentUser()
		if err != nil {
			c.String(http.StatusInternalServerError, fmt.Sprintf("error: %s", err))
			return
		}

		playlists, err := client.GetPlaylistsForUser(user.ID)
		if err != nil {
			c.String(http.StatusInternalServerError, fmt.Sprintf("error: %s", err))
			return
		}

		var matchedPlaylists []string
		var matchedTracks []string

		for _, playlist := range playlists.Playlists {
			rawTracks, _ := client.GetPlaylistTracks(playlist.ID)

			for _, track := range rawTracks.Tracks {
				trackName := track.Track.Name
				re := regexp.MustCompile("(?i)" + trackNameQuery)
				if re.MatchString(trackName) {
					matchedPlaylists = append(matchedPlaylists, playlist.Name)
					matchedTracks = append(matchedTracks, track.Track.Name)
				}
			}
		}

		c.JSON(http.StatusOK, gin.H{
			"user:":              user,
			"playlists searched": len(playlists.Playlists),
			"matchedPlaylists":   matchedPlaylists,
			"matchedTracks":      matchedTracks,
		})
	})

	r.Static("/app", "./static")

	r.Run() // listen and serve on 0.0.0.0:8080 (for windows "localhost:8080")
}
