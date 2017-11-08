module Main exposing (..)

import Html exposing (div, Html, text)
import Html.Attributes
import Html.Events exposing (..)
import WebSocket
import Json.Encode exposing (object, encode)
import Json.Decode exposing (int, field, list, Decoder, decodeString)
import Json.Decode.Pipeline exposing (decode, required, optional, hardcoded)


main =
    Html.program
        { init = init
        , view = view
        , update = update
        , subscriptions = subscriptions
        }


host =
    "127.0.0.1"


url =
    "ws://" ++ host ++ ":7700/colormonosequencer"



-- MODEL


baseDo : Int
baseDo =
    60


re =
    baseDo + 2

mi =
    baseDo + 4

fa =
    baseDo + 5

intToPitch x =
    case x of
        baseDo ->
            Do

        re ->
            Re

        _ ->
            Fa


pitchToInt : Pitch -> Int
pitchToInt pitch =
    case pitch of
        Do ->
            baseDo

        Re ->
            baseDo + 2

        Mi ->
            baseDo + 4

        Fa ->
            baseDo + 5


type Pitch
    = Do
    | Re
    | Mi
    | Fa


type alias Note =
    { pitch : Pitch
    }


type alias Model =
    { notes : List Note
    }


init : ( Model, Cmd Msg )
init =
    ( Model [ Note Do, Note Re, Note Mi, Note Fa ], WebSocket.send url <| encode 0 getState )



-- UPDATE


type Msg
    = ChangeNote Int
    | RcvState String


update : Msg -> Model -> ( Model, Cmd Msg )
update msg model =
    case msg of
        ChangeNote i ->
            ( model, WebSocket.send url <| toString i )

        RcvState str ->
            ( model, Cmd.none )



-- SUBSCRIPTIONS


subscriptions : Model -> Sub Msg
subscriptions model =
    WebSocket.listen url RcvState



-- VIEW


view : Model -> Html Msg
view model =
    div [] []


viewMessage : String -> Html msg
viewMessage msg =
    div [] [ text msg ]



-- COMMANDS


type alias BeatMsg =
    { payload : BeatMsgPayload
    }


type alias BeatMsgPayload =
    { rthythmIndex : Int
    , noteIndex : Int
    }


type alias StateMsgPayload =
    { pitches : List Int
    , rhythm : List Int
    }


type alias StateMsg =
    { payload : StateMsgPayload
    }


type WSMsg
    = Beat
    | State


getState : Json.Encode.Value
getState =
    object [ ( "kind", Json.Encode.string "state" ) ]


determineTypeOfWSMsg : String -> WSMsg
determineTypeOfWSMsg msg =
    case decodeString (field "kind" Json.Decode.string) msg of
        Ok "state" ->
            State

        Ok "beat" ->
            Beat

        _ ->
            Debug.crash "Unexpected msg kind!"


decodeBeatMsg : Decoder BeatMsg
decodeBeatMsg =
    let
        payloadDecoder =
            decode BeatMsgPayload
                |> required "rhythmIndex" int
                |> required "noteIndex" int
    in
        decode BeatMsg
            |> required "payload" payloadDecoder


decodeStateMsg : Decoder StateMsg
decodeStateMsg =
    let
        payloadDecoder =
            decode StateMsgPayload
                |> required "pitches" (list int)
                |> required "rhythm" (list int)
    in
        decode StateMsg
            |> required "payload" payloadDecoder


decodeWSMsg : String -> Model -> Model
decodeWSMsg msg =
    let
        kind =
            determineTypeOfWSMsg msg

        updateBeat : BeatMsg -> Model -> Model
        updateBeat beat model =
            model

        updateState : StateMsg -> Model -> Model
        updateState newState model =
            { model | notes = newState.payload.pitches }

        payloadDecoder =
            case kind of
                State ->
                    case decodeString decodeStateMsg msg of
                        Ok msg ->
                            updateState msg

                        _ ->
                            Debug.crash ""

                Beat ->
                    case decodeString decodeBeatMsg msg of
                        Ok msg ->
                            updateBeat msg

                        _ ->
                            Debug.crash ""
    in
        \x -> x
