module Main exposing (..)

import Html.Attributes exposing (..)
import Html.Events exposing (..)
import WebSocket
import Html exposing (..)
import Json.Encode as JE


main =
    Html.program
        { init = init
        , view = view
        , update = update
        , subscriptions = subscriptions
        }



-- MODEL


type alias NewBug =
    { pitch : Int
    , kind : Int
    }


type alias Model =
    { message : String
    , newBug : NewBug
    }


init : ( Model, Cmd Msg )
init =
    ( Model
        ""
        { pitch = 0, kind = 0 }
    , Cmd.none
    )


bugToJSON : NewBug -> String
bugToJSON bug =
    let
        obj =
            JE.object
                [ ( "pitch", JE.int bug.pitch )
                , ( "kind", JE.int bug.kind )
                ]
    in
        JE.encode 0 obj


wsMsg : WsMsgKind -> Maybe String -> String
wsMsg kind payload =
    let
        kindString =
            wsMsgKindToString kind

        toPayload =
            Maybe.withDefault "" payload

        obj =
            JE.object [ ( "kind", JE.string kindString ), ( "payload", JE.string toPayload ) ]
    in
        JE.encode 0 obj



-- UPDATE


type WsMsgKind
    = Ping
    | Create
    | Ding


wsMsgKindToString : WsMsgKind -> String
wsMsgKindToString kind =
    case kind of
        Ping ->
            "ping"

        Create ->
            "create"

        Ding ->
            "ding"


type Msg
    = Send WsMsgKind
    | NewMessage String


update : Msg -> Model -> ( Model, Cmd Msg )
update msg model =
    case msg of
        Send kind ->
            let
                payload =
                    case kind of
                        Ping ->
                            Nothing

                        Create ->
                            Just (bugToJSON model.newBug)

                        Ding ->
                            Nothing
            in
                ( model, WebSocket.send "ws://127.0.0.1:7700" <| wsMsg kind payload )

        NewMessage str ->
            ( { model | message = str }, Cmd.none )



-- SUBSCRIPTIONS


subscriptions : Model -> Sub Msg
subscriptions model =
    WebSocket.listen "ws://127.0.0.1:7700" NewMessage



-- VIEW


view : Model -> Html Msg
view model =
    div []
        [ viewMessage model.message
        , button [ onClick <| Send Ping ] [ text "Send" ]
        ]


viewMessage : String -> Html msg
viewMessage msg =
    div [] [ text msg ]
