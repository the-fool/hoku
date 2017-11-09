port module Main exposing (..)

import Html exposing (div, Html, text)
import Html.Attributes exposing (class, id)
import Html.Events exposing (onClick)
import WebSocket
import Json.Encode exposing (object, encode)
import Json.Decode exposing (int, field, list, Decoder, decodeString)
import Json.Decode.Pipeline exposing (decode, required, optional, hardcoded)


port beat : Int -> Cmd msg


type alias Flags =
    { websocketHost : String }


main : Program Flags Model Msg
main =
    Html.programWithFlags
        { init = init
        , view = view
        , update = update
        , subscriptions = subscriptions
        }



-- MODEL


type alias Model =
    { notes : List PitchIndex
    , wsurl : String
    }


type alias PitchIndex =
    Int


numOctaves =
    2


numPitches =
    7 * 2


init : Flags -> ( Model, Cmd Msg )
init fs =
    let
        url host =
            host ++ ":7700/colormonosequencer"

        wsurl =
            Debug.log "url" (url fs.websocketHost)
    in
        ( Model [] wsurl, WebSocket.send wsurl <| encode 0 getStateWSMsg )



-- UPDATE


type Msg
    = ChangeNote Int PitchIndex
    | RcvMsg String


update : Msg -> Model -> ( Model, Cmd Msg )
update msg model =
    case msg of
        ChangeNote i pitch ->
            ( updateNotes i pitch model, WebSocket.send model.wsurl <| encode 0 <| changePitchWSMsg i pitch )

        RcvMsg wsmsg ->
            onReceiveWSMsg wsmsg model


onReceiveWSMsg : String -> Model -> ( Model, Cmd Msg )
onReceiveWSMsg wsmsg model =
    case decodeString (field "action" Json.Decode.string) wsmsg of
        Ok "state" ->
            ( updateState wsmsg model, Cmd.none )

        Ok "beat" ->
            let
                cmd =
                    case decodeString decodeBeatMsg wsmsg of
                        Ok b ->
                            beat b.payload.noteIndex

                        _ ->
                            Debug.crash "error decoding beat"
            in
                ( model, cmd )

        _ ->
            Debug.crash "unknow msg action"


updateNotes : Int -> PitchIndex -> Model -> Model
updateNotes index newPitch model =
    let
        newNote i note =
            if i == index then
                newPitch
            else
                note
    in
        { model | notes = List.indexedMap newNote model.notes }



-- SUBSCRIPTIONS


subscriptions : Model -> Sub Msg
subscriptions model =
    WebSocket.listen model.wsurl RcvMsg



-- VIEW


view : Model -> Html Msg
view model =
    div [ class "container" ] [ viewNotes model.notes ]


viewNotes : List PitchIndex -> Html Msg
viewNotes notes =
    div [ class "notes" ] (List.indexedMap viewNote notes)


viewNote : Int -> PitchIndex -> Html Msg
viewNote i pitchIndex =
    let
        cyclePitch pitchIndex =
            (pitchIndex + 1) % numPitches

        noteId =
            "note-" ++ (toString i)

        newPitch =
            cyclePitch pitchIndex
    in
        div
            [ class "note"
            , id noteId
            , onClick <| ChangeNote i newPitch
            ]
            [ text <| toString <| pitchIndex ]



-- COMMANDS


changePitchWSMsg : Int -> Int -> Json.Encode.Value
changePitchWSMsg index value =
    object
        [ ( "kind", Json.Encode.string "pitch" )
        , ( "payload"
          , object
                [ ( "index", Json.Encode.int index )
                , ( "value", Json.Encode.int value )
                ]
          )
        ]


getStateWSMsg : Json.Encode.Value
getStateWSMsg =
    object [ ( "kind", Json.Encode.string "state" ) ]


type alias BeatMsg =
    { payload : BeatMsgPayload
    }


type alias BeatMsgPayload =
    { rhythmIndex : Int
    , noteIndex : Int
    }


type alias StateMsgPayload =
    { pitches : List Int
    , rhythm : List Int
    }


type alias StateMsg =
    { payload : StateMsgPayload
    }


decodeBeatMsg : Decoder BeatMsg
decodeBeatMsg =
    let
        payloadDecoder =
            decode BeatMsgPayload
                |> required "rhythm_index" int
                |> required "note_index" int
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


updateState : String -> Model -> Model
updateState msg =
    let
        updateState newState model =
            { model | notes = newState.payload.pitches }

        payloadDecoder =
            case decodeString decodeStateMsg msg of
                Ok msg ->
                    updateState msg

                _ ->
                    Debug.crash ""
    in
        payloadDecoder
